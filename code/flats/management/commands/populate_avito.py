import re

from django.conf import settings
from django.core.management import BaseCommand

from bs4 import BeautifulSoup
import requests

from ...models import Flat


class Command(BaseCommand):
    type = 'avito'
    domain = 'https://www.avito.ru'

    url = domain + '/sankt-peterburg/kvartiry/prodam?' \
        'p={p}&pmax={max_price}&s=1&metro={metro_stations}&f=59_13988b'

    def add_arguments(self, parser):
        parser.add_argument('--max-price', type=int, default=8000000)

    def parse_page(self, bs):
        flats = []

        for _, row in enumerate(bs.find_all(class_='js-catalog-item-enum')):
            link = row.select_one('.snippet-link')
            if not row.select_one('[data-marker="item-price"]'):
                continue

            price = int(re.sub(
                r'[^\d]',
                '',
                row.select_one('[data-marker="item-price"]').text,
            ))

            title = link.string.strip()
            r = re.search(r'(?P<square>\d+) м²', title)
            if r:
                square = float(r.group('square'))
            else:
                continue
            price_by_m = price / square
            url = self.domain + link['href']

            print(title)
            r = re.match(r'(\d+).*', title)
            if r:
                rooms = int(r.group(1))
            else:
                rooms = 0

            addr_item = row.select_one('.address')
            address = addr_item.select_one(
                '.item-address__string',
            ).text.strip('\n \t,')
            metro = addr_item.select_one(
                '.item-address-georeferences-item__content',
            ).text
            if not re.search('[А-Яа-я]', address):
                # fake
                continue

            try:
                distance_str = addr_item.select_one(
                    '.item-address-georeferences-item__after',
                ).string
            except AttributeError:
                distance = 0
            else:
                if distance_str.endswith(' км'):
                    try:
                        distance = int(
                            float(distance_str.replace(
                                ' км',
                                '',
                            ).strip()) * 1000
                        )
                    except ValueError:
                        distance = 500
                else:
                    distance = int(distance_str.replace(' м', '').strip())

            r = re.match(r'.*?_(\d+)$', url)
            source_id = int(r.group(1))

            print(title)
            r = re.match(r'.*?(\d+)/(\d+) эт\.$', title)
            floor = int(r.group(1))
            total_floors = int(r.group(2))

            flats.append(Flat(
                title=title,
                address=address,
                metro=metro,
                distance=distance,
                square=square,
                rooms=rooms,
                price=price,
                price_by_m=price_by_m,
                url=url,
                floor=floor,
                total_floors=total_floors,
                source_type=self.type,
                source_id=source_id,
            ))
        return flats

    def handle(self, *args, **options):

        r = requests.get(self.url.format(
            p=1,
            max_price=options['max_price'],
            metro_stations=settings.AVITO_METRO_STATIONS,
        ))

        bs = BeautifulSoup(r.text, 'html.parser')  # 'html5lib'
        flats = self.parse_page(bs)

        pagination = bs.select_one('[data-marker="pagination-button"]')
        spans = pagination.select('span')[1:-1]
        if spans:
            last_page = int(spans[-1].text)
        else:
            last_page = 1
        print(last_page)

        for page in range(2, last_page):
            next_page = self.url.format(
                p=page,
                max_price=options['max_price'],
                metro_stations=settings.AVITO_METRO_STATIONS,
            )
            r = requests.get(next_page)
            bs = BeautifulSoup(r.text, 'html.parser')  # 'html5lib'
            flats.extend(self.parse_page(bs))

        Flat.objects.filter(source_type=self.type).delete()
        Flat.objects.bulk_create(flats)

        self.stdout.write(str(len(flats)))
