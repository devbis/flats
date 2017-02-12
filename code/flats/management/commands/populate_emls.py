import re

from django.conf import settings
from django.core.management import BaseCommand

from bs4 import BeautifulSoup
import requests

from ...models import Flat


class Command(BaseCommand):
    type = 'emls'
    domain = 'http://www.emls.ru'

    url = domain + '/flats/?query=s/1/pmax/{max_price}/' \
                   'is_auction/2/place/address/reg/2/dept/2/metro/map/' \
                   'tr[]/{metro_stations}/' \
                   'nearm/3/sort1/1/dir1/2/sort2/3/dir2/1/interval/3'

    def add_arguments(self, parser):
        parser.add_argument('--max-price', type=int, default=8000000)

    def parse_page(self, bs):
        flats = []

        for _, row in enumerate(bs.select('.listing .row')):
            try:
                link = row['data-href']
            except KeyError:
                continue

            url = self.domain + link
            address = row.select_one('.address-geo').text.strip()

            title = row.select_one('.w-image > div:nth-of-type(2)').text.strip()
            square = float(row.select_one('.space-all').text)
            price = int(
                row.select_one('.pricing .price').text[:-1].replace(' ', '')
            )
            price_by_m = int(price // square)

            print(title)
            r = re.match(r'(\d+).*', title)
            if r:
                rooms = int(r.group(1))
            else:
                rooms = 0

            dist = row.select_one('.w-addr > .ellipsis').findAll(text=True)[0]

            if isinstance(dist, str):
                if dist.endswith(' километра'):
                    try:
                        distance = int(
                            float(dist.replace(' километра', '')) * 1000
                        )
                    except ValueError:
                        distance = 500
                else:
                    distance = int(dist.replace(' метров', '').replace(' ', ''))
            else:
                print(dist)
                distance = 0

            r = re.match(r'.*?/(\d+)\.html$', url)
            source_id = int(r.group(1))

            fl = row.select_one('.w-floor b').text
            print(title)
            r = re.match(r'.*?(\d+)/(\d+) этаж$', fl)
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
                source_type=self.type,
                source_id=source_id,
            ))
        return flats

    def handle(self, *args, **options):
        headers = {'user-agent': 'google crawler/0.0.1'}

        r = requests.get(self.url.format(
            max_price=options['max_price'] // 1000,
            metro_stations=settings.EMLS_METRO_STATIONS,
        ), headers=headers)

        bs = BeautifulSoup(r.text, 'html.parser')  # 'html5lib'
        flats = self.parse_page(bs)

        next_page = bs.select('.pages a.button-2')[-1]['href']

        while next_page:
            r = requests.get(self.domain + next_page, headers=headers)
            bs = BeautifulSoup(r.text, 'html.parser')  # 'html5lib'
            try:
                next_page = bs.select('.pages a.button-2')[-1]['href']
            except IndexError:
                next_page = None
            flats.extend(self.parse_page(bs))

        Flat.objects.filter(source_type=self.type).delete()
        Flat.objects.bulk_create(flats)

        self.stdout.write(str(len(flats)))
