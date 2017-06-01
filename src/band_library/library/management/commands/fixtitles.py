# Full path and name to your csv file
#csv_filepathname = "/home/mitch/projects/wantbox.com/wantbox/zips/data/zipcodes.csv"
# Full path to your django project directory
import sys, os, csv
from django.core.management.base import BaseCommand, CommandError
from library.models import Entry, Author, Category, Instrument

catcache = {}

def folder(dirname):
    if os.path.isdir(dirname):
        return os.listdir(dirname)
    else:
        return None

class Command(BaseCommand):
    help = 'Fix titles'


    def handle(self, *args, **options):
        eee = Entry.objects.filter(title__istartswith='the ')
        for eeeo in eee:
            eeea = eeeo.title.split();
            newtitle = ' '.join(eeea[1:]) + ", The"
            print >>sys.stderr, "Change: %s to %s" % (eeeo.title, newtitle)
            eeeo.title = newtitle
            eeeo.save()
            
        eee = Entry.objects.filter(title__istartswith='a ')
        for eeeo in eee:
            eeea = eeeo.title.split();
            newtitle = ' '.join(eeea[1:]) + ", A"
            print >>sys.stderr, "Change: %s to %s" % (eeeo.title, newtitle)
            eeeo.title = newtitle
            eeeo.save()


