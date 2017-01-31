import re
import json

from django.core.management import BaseCommand

from bs4 import BeautifulSoup
import requests

from ...models import Flat


class Command(BaseCommand):
    domain = 'https://www.avito.ru'

    url = domain + \
        '/sankt-peterburg/kvartiry/prodam?' \
        'pmax={max_price}&s=1&' \
        'metro=157-160-164-165-174-176-180-185-191-199-201-202-205-206-209-' \
        '210-1015-1016-2132&' \
        'f=59_13988b'

    def add_arguments(self, parser):
        parser.add_argument('--max-price', type=int, default=8000000)

    def parse_page(self, bs):
        flats = []

        for _, row in enumerate(bs.find_all(class_='js-catalog-item-enum')):
            link = row.select_one('.item-description-title-link')
            if not row.select_one('.popup-prices'):
                continue

            prices = json.loads(row.select_one('.popup-prices')['data-prices'])

            title = link.string.strip()
            price = prices[0]['currencies']['RUB']
            price_by_m = prices[1]['currencies']['RUB']
            square = price / price_by_m
            url = self.domain + link['href']

            print(title)
            r = re.match(r'(\d+).*', title)
            if r:
                rooms = int(r.group(1))
            else:
                rooms = 0

            addr = list(row.select_one('.address').descendants)
            address = addr[-1].strip('\n \t,')
            if not re.search('[А-Яа-я]', address):
                # fake
                continue

            if isinstance(addr[-2], str):
                if addr[-2].endswith(' км'):
                    try:
                        distance = int(
                            float(addr[-2].replace(' км', '')) * 1000
                        )
                    except ValueError:
                        distance = 500
                else:
                    distance = int(addr[-2].replace(' м', ''))
            else:
                print(addr)
                distance = 0

            r = re.match(r'.*?_(\d+)$', url)
            source_id = int(r.group(1))

            print(title)
            r = re.match(r'.*?(\d+)/(\d+) эт\.$', title)
            floor = int(r.group(1))
            total_floors = int(r.group(2))

            flats.append(Flat(
                title=title,
                address=address,
                distance=distance,
                square=square,
                rooms=rooms,
                price=price,
                price_by_m=price_by_m,
                url=url,
                floor=floor,
                total_floors=total_floors,
                source_type='avito',
                source_id=source_id,
            ))
        return flats

    def handle(self, *args, **options):

        r = requests.get(self.url.format(max_price=options['max_price']))

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

        Flat.objects.filter(source_type='avito').delete()
        Flat.objects.bulk_create(flats)

        self.stdout.write(str(len(flats)))
