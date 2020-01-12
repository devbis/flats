from flats.utils import find_plan_avito
from ...models import Flat

from django.core.management import BaseCommand

import requests


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            default='https://www.avito.ru/sankt-peterburg/kvartiry/'
            '3-k_kvartira_52_m_24_et._917626230'
        )
        parser.add_argument(
            '--id',
            default='https://www.avito.ru/sankt-peterburg/kvartiry/'
            '3-k_kvartira_52_m_24_et._917626230'
        )

    def handle(self, *args, **options):
        # plan = find_plan_avito(
        #     'https://www.avito.ru/sankt-peterburg/kvartiry/z_' +
        #     options['id']
        # )
        #
        # print(plan)

        # r = requests.get(options['url'])
        # # r = requests.get(
        # #     'https://www.avito.ru/sankt-peterburg/kvartiry/z_' +
        # #     options['id']
        # # )
        # r = requests.get(url)
        # bs = BeautifulSoup(r.text, 'html.parser')  # 'html5lib'
        #
        # max_brightness = 0.0
        # max_white_url = None
        # # for im in bs.select('div.gallery-img-frame'):
        # #     image_url = 'https:' + im['data-url']
        # #     response = requests.get(image_url, stream=True)
        # #     img = Image.open(response.raw)
        # #     print(img)
        #
        # # thumbnails
        # for im in bs.select('.gallery-list-item-link'):
        #     image_url = 'https:' + re.findall('url\((.*?)\)', im['style'])[0]
        #     response = requests.get(image_url, stream=True)
        #     img = Image.open(response.raw)
        #     img = img.convert('L')
        #     color_total = 0
        #     total = len(img.getdata())
        #     for pix in img.getdata():
        #         color_total += pix
        #
        #     brightness = color_total/255/total
        #     if brightness > 0.75 and brightness > max_brightness:
        #         max_brightness = brightness
        #         max_white_url = image_url
        #     print(max_brightness, brightness)
        #
        # dir = 'static/plans/'
        # filename = max_white_url.rsplit('/', maxsplit=1)[1]
        # r = requests.get(max_white_url, stream=True)
        # if r.status_code == 200:
        #     with open(dir + filename, 'wb') as f:
        #         for chunk in r.iter_content(1024):
        #             f.write(chunk)
        # #
        # # print(max_white_url)
        # # image = images[0]
        # # self.stdout.write(image)

        self.populate_flats()

    def populate_flats(self):
        flats = Flat.objects.filter(source_type='avito')
        for flat in flats:
            url = flat.url

            plan = find_plan_avito(url)
            if plan:
                dir = 'static/plans/'
                filename = '{}.jpg'.format(flat.id)
                # plan.rsplit('/', maxsplit=1)[1]
                r = requests.get(plan, stream=True)
                if r.status_code == 200:
                    with open(dir + filename, 'wb') as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)

            print('{}: {}'.format(url, plan))
