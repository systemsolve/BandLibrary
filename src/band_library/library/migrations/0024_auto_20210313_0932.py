# Generated by Django 2.2.17 on 2021-03-12 22:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0023_auto_20210313_0927'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='title',
            field=models.CharField(default='Title of Performance', max_length=200, verbose_name='Title/Theme'),
        ),
        migrations.AlterField(
            model_name='program',
            name='venue',
            field=models.CharField(default='Venue of Performance', max_length=200),
        ),
    ]
