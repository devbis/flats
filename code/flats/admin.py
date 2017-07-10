import urllib.parse

from django.contrib import admin
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import F
from django.utils.html import format_html

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
                ).exclude(address__icontains='поселок').\
                    exclude(address__icontains='п.г.т.')
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
        'price_print', 'price_by_m2', 'square', 'link', 'address', 'metro',
        'map', 'distance', 'floor', 'total_floors', 'source_type',
    ]
    list_filter = [FarListFilter, FloorFilter, 'rooms', 'source_type', 'metro']

    def price_print(self, obj: Flat):
        return intcomma(obj.price)
    price_print.admin_order_field = 'price'
    price_print.short_description = 'Price'

    def price_by_m2(self, obj: Flat):
        return intcomma(obj.price_by_m)
    price_by_m2.admin_order_field = 'price_by_m'

    def link(self, obj: Flat):
        return format_html('<a href="{0}" target="_blank">{0}</a>', obj.url)

    def map(self, obj: Flat):
        return format_html(
            '<a href="https://www.google.ru/maps/place/{},+Санкт-Петербург'
            '" target="_blank"><img src="http://icons.iconarchive.com/'
            'icons/paomedia/small-n-flat/32/map-marker-icon.png" '
            'alt="map"></a>',
            urllib.parse.quote_plus(obj.address),
        )
