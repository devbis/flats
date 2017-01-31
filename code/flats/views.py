from django.views import generic

from flats.models import Flat


class IndexView(generic.ListView):
    model = Flat
    context_object_name = 'flats'
