# Generated by Django 2.2.24 on 2021-09-30 06:27

from django.db import migrations

def set_mediatype(apps, schema_editor):
    EntryMedia = apps.get_model("library", "EntryMedia")
    thefiles = EntryMedia.objects.filter(mfile__iendswith=".pdf")
    # this runs in a transaction by default
    for afile in thefiles:
        afile.mtype = 'PDF'
        afile.save()
    

def no_op(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0044_entrymedia_mtype'),
    ]

    operations = [
        migrations.RunPython(set_mediatype, no_op)
    ]