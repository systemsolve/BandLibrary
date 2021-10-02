# Generated by Django 2.2.23 on 2021-09-20 06:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0033_auto_20210920_1608'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='fee',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='Fee (AUD)'),
        ),
        migrations.AddField(
            model_name='entry',
            name='saleable',
            field=models.BooleanField(default=False, verbose_name='Ready for sale'),
        ),
    ]