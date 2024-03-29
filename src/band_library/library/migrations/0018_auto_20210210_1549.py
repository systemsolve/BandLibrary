# Generated by Django 2.2.17 on 2021-02-10 04:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0017_asset_assetcondition_assetmaker_assetmodel_assettype'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='owner',
            field=models.CharField(blank=True, help_text='Actual owner if not Oakleigh Brass', max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='location',
            field=models.TextField(blank=True, help_text='Name/address of borrower or place', null=True),
        ),
    ]
