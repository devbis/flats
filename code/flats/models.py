from django.db import models


class Flat(models.Model):
    title = models.CharField(max_length=1024)
    square = models.DecimalField(max_digits=10, decimal_places=2)
    rooms = models.IntegerField()
    price = models.IntegerField()
    price_by_m = models.IntegerField()
    url = models.URLField()
    address = models.TextField()
    metro = models.TextField(default='')
    distance = models.IntegerField()
    floor = models.IntegerField()
    total_floors = models.IntegerField()
    source_type = models.CharField(max_length=255)
    source_id = models.IntegerField()

    def __str__(self):
        return f"{self.square}m, {self.rooms} rooms, {self.price//1000:d}"
