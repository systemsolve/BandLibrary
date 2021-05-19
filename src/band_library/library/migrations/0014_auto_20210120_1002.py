# Generated by Django 2.2.17 on 2021-01-19 23:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0013_seealso'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seealso',
            name='source_entry',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='related_entries', to='library.Entry'),
        ),
    ]
