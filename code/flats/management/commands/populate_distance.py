from flats.utils import real_distance_to_subway
from ...models import Flat

from django.core.management import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--city', default='190000, Санкт-Петербург')

    def handle(self, *args, **options):
        flats = Flat.objects.all()
        for flat in flats:
            real = real_distance_to_subway(
                flat.address,
                flat.metro,
                options['city'],

            )
            print(flat, flat.address, real)
            if real:
                flat.real_distance = real['distance']
                flat.debug_url = real['url']
                flat.save()
