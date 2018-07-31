import re
import json

from django.conf import settings
from django.core.management import BaseCommand

from bs4 import BeautifulSoup
import requests

from ...models import Flat


class Command(BaseCommand):
    type = 'avito'
    domain = 'https://www.avito.ru'

    url = domain + '/sankt-peterburg/kvartiry/prodam?' \
        'pmax={max_price}&s=1&metro={metro_stations}&f=59_13988b'

    def add_arguments(self, parser):
        parser.add_argument('--max-price', type=int, default=8000000)

    def parse_page(self, bs):
        flats = []

        for _, row in enumerate(bs.find_all(class_='js-catalog-item-enum')):
            link = row.select_one('.item-description-title-link')
            if not row.select_one('.popup-prices'):
                continue

            prices = json.loads(row.select_one('.popup-prices')['data-prices'])

            title = link.select_one('span').string.strip()
            price = prices[0]['currencies']['RUB']
            price_by_m = prices[1]['currencies']['RUB']
            square = price / (price_by_m or 1)
            url = self.domain + link['href']

            print(title)
            r = re.match(r'(\d+).*', title)
            if r:
                rooms = int(r.group(1))
            else:
                rooms = 0

            addr_item = row.select_one('.address')
            addr = list(addr_item.descendants)
            metro = addr[2].strip('\n \t,').split(',')[0]
            address = addr[-1].strip('\n \t,')
            if not re.search('[А-Яа-я]', address):
                # fake
                continue

            try:
                distance_str = addr_item.select_one('.c-2').string
            except AttributeError:
                distance = 0
            else:
                if distance_str.endswith(' км'):
                    try:
                        distance = int(
                            float(distance_str.replace(' км', '')) * 1000
                        )
                    except ValueError:
                        distance = 500
                else:
                    distance = int(distance_str.replace(' м', ''))

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
            max_price=options['max_price'],
            metro_stations=settings.AVITO_METRO_STATIONS,
        ))

        bs = BeautifulSoup(r.text, 'html.parser')  # 'html5lib'
        flats = self.parse_page(bs)

        next_page = bs.select_one('a.js-pagination-next')['href']

        while next_page:
            r = requests.get(self.domain + next_page)
            bs = BeautifulSoup(r.text, 'html.parser')  # 'html5lib'
            try:
                next_page = bs.select_one('a.js-pagination-next')['href']
            except TypeError:
                next_page = None
            flats.extend(self.parse_page(bs))

        Flat.objects.filter(source_type=self.type).delete()
        Flat.objects.bulk_create(flats)

        self.stdout.write(str(len(flats)))
