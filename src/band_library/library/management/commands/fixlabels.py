# Full path and name to your csv file
#csv_filepathname = "/home/mitch/projects/wantbox.com/wantbox/zips/data/zipcodes.csv"
# Full path to your django project directory
import sys, os, csv
from django.core.management.base import BaseCommand, CommandError
from library.models import Entry, Author, Category, Instrument
from library.utilx import error_log

catcache = {}

def folder(dirname):
    if os.path.isdir(dirname):
        return os.listdir(dirname)
    else:
        return None

class Command(BaseCommand):
    help = 'Fix labels'

    def handle(self, *args, **options):
        eee = Entry.objects.filter(callno__contains='.')
        for eeeo in eee:
            lll = eeeo.callno.split('.')
            ooo = "%d.%02d" % (int(lll[0]), int(lll[1]))
            error_log("Change: %s to %s" % (eeeo.callno, ooo))
            eeeo.callno = ooo
            eeeo.save()


