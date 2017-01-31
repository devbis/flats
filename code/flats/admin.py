import locale
import urllib.parse

from django.contrib import admin
from django.db.models import F

from .models import Flat


class FarListFilter(admin.SimpleListFilter):
    limit = 3000
    floor_limit = 15

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == '1':
                return queryset.filter(
                    distance__gt=self.limit,
                    total_floors__gt=self.floor_limit,
                )
            else:
                return queryset.filter(
                    distance__lte=self.limit,
                    total_floors__lte=self.floor_limit,
                ).exclude(address__contains='поселок')
        else:
            return queryset

    def lookups(self, request, model_admin):
        return (
            ('1', 'Yes'),
            ('0', 'No'),
        )

    title = 'distance'
    parameter_name = 'is_far'


class FloorFilter(admin.SimpleListFilter):
    limit = 3000
    floor_limit = 15

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == '!1':
                return queryset.filter(
                    floor__gte=2
                )
            elif self.value() == '!max':
                return queryset.filter(
                    floor__lt=F('total_floors')
                )
            else:
                return queryset.filter(
                    floor__gte=2,
                    floor__lt=F('total_floors')
                )
        else:
            return queryset

    def lookups(self, request, model_admin):
        return (
            ('!1', '> 1'),
            ('!max', 'Not last'),
            ('!1!max', 'Not last > 1'),
        )

    title = 'floor'
    parameter_name = 'floor'


@admin.register(Flat)
class FlatAdmin(admin.ModelAdmin):
    list_display = [
        'price', 'price_by_m', 'link', 'address', 'map', 'distance', 'floor',
        'total_floors',
    ]
    list_filter = [FarListFilter, FloorFilter, 'rooms']

    def price_by_m2(self, obj: Flat):
        return locale.format("%d", obj.price_by_m, True)

    def link(self, obj: Flat):
        return '<a href="{0}" target="_blank">{0}</a>'.format(obj.url)
    link.allow_tags = True

    def map(self, obj: Flat):
        return '<a href="https://www.google.ru/maps/place/{},+Санкт-Петербург' \
               '" target="_blank"><img src="http://icons.iconarchive.com/' \
               'icons/paomedia/small-n-flat/32/map-marker-icon.png" ' \
               'alt="map"></a>'.format(urllib.parse.quote_plus(obj.address))
    map.allow_tags = True
