# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-31 02:10


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0005_auto_20170529_0318'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='author',
            options={'ordering': ['surname', 'given']},
        ),
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['label'], 'verbose_name_plural': 'Categories'},
        ),
        migrations.AlterModelOptions(
            name='entry',
            options={'ordering': ['title', 'composer__surname'], 'verbose_name_plural': 'Entries'},
        ),
        migrations.AlterModelOptions(
            name='instrument',
            options={'ordering': ['name']},
        ),
        migrations.AddField(
            model_name='entry',
            name='media',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='entry',
            name='added',
            field=models.DateField(auto_now=True, verbose_name='Date added'),
        ),
        migrations.AlterField(
            model_name='entry',
            name='duration',
            field=models.CharField(default='0:0', max_length=8),
        ),
        migrations.AlterUniqueTogether(
            name='author',
            unique_together=set([('surname', 'given')]),
        ),
    ]
