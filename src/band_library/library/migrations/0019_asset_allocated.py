# Generated by Django 2.2.17 on 2021-02-10 05:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0018_auto_20210210_1549'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='allocated',
            field=models.BooleanField(default=False, verbose_name='Allocated/In Use'),
        ),
    ]
