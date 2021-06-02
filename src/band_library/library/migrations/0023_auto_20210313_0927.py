# Generated by Django 2.2.17 on 2021-03-12 22:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0022_auto_20210310_1428'),
    ]

    operations = [
        migrations.RenameField(
            model_name='program',
            old_name='included',
            new_name='performance_date',
        ),
        migrations.RemoveField(
            model_name='program',
            name='entry',
        ),
        migrations.AddField(
            model_name='program',
            name='venue',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.CreateModel(
            name='ProgramItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comments', models.TextField(blank=True, null=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='performances', to='library.Entry')),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='library.Program')),
            ],
        ),
    ]