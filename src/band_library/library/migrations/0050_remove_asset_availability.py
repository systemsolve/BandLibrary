# Generated by Django 3.2.13 on 2024-09-28 01:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0049_asset_availability'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='asset',
            name='availability',
        ),
    ]
