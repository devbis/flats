# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-07-08 20:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flats', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='flat',
            name='metro',
            field=models.TextField(default=''),
        ),
    ]