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
    help = 'Imports media named from files'

    def add_arguments(self, parser):
        parser.add_argument('scandir', type=folder)

    def handle(self, *args, **options):
        entries = options['scandir']
        for prow in entries:
            base = os.path.splitext(os.path.basename(prow))[0]
            matched = False
            checks = []
            for schar in ('_', '-', ','):
                bases = base.split(schar)
                #print >>sys.stderr, "LINE: %s" % base
                eee = Entry.objects.filter(title__istartswith=bases[0]).first()
                if eee:
                    matched = True
                    if not eee.media:
                        error_log("IMPORT: %s" % str(eee))
                        eee.media = os.path.basename(prow)
                        eee.save()                        
                    else:
                        error_log("MATCH: %s" % str(eee))
                    break
                else:
                    checks.append(bases[0])
                    
            if not matched:
                error_log("UNMATCHED: '%s'" % str(checks))
            
            