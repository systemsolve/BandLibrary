# Generated by Django 2.2.23 on 2021-06-02 08:26

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0028_auto_20210602_1421'),
    ]

    operations = [
        migrations.AddField(
            model_name='folder',
            name='issue_date',
            field=models.DateField(default=datetime.date(2021, 5, 1)),
            preserve_default=False,
        ),
    ]