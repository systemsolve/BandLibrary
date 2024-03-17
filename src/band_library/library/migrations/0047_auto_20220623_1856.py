# Generated by Django 3.2.13 on 2022-06-23 08:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0046_auto_20220622_1954'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssetPurpose',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=128, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='AssetStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=128)),
                ('comments', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='AssetSubType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=128)),
                ('comments', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='asset',
            name='comments',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='AssetMedia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mfile', models.FileField(max_length=256, upload_to='', verbose_name='Filename')),
                ('mtype', models.CharField(choices=[('PDF', 'PDF'), ('IMAGE', 'Image'), ('VIDEO', 'Video'), ('AUDIO', 'Audio'), ('OTHER', 'Other/Unknown')], default='OTHER', max_length=8, verbose_name='Media Type')),
                ('comment', models.CharField(blank=True, max_length=128, null=True)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='related_media', to='library.asset')),
                ('purpose', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='library.assetpurpose')),
            ],
            options={
                'verbose_name': 'Supporting media',
                'verbose_name_plural': 'Supporting media',
            },
        ),
        migrations.AddField(
            model_name='asset',
            name='asset_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assets', to='library.assetstatus'),
        ),
        migrations.AddField(
            model_name='asset',
            name='asset_subtype',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assets', to='library.assetsubtype'),
        ),
    ]
