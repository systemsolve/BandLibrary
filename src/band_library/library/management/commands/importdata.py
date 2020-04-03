# Full path and name to your csv file
#csv_filepathname = "/home/mitch/projects/wantbox.com/wantbox/zips/data/zipcodes.csv"
# Full path to your django project directory
import sys, os, csv
from django.core.management.base import BaseCommand, CommandError
from library.models import Entry, Author, Category, Instrument

catcache = {}

class Command(BaseCommand):
    help = 'Imports CSV Library Data'

    def add_arguments(self, parser):
        parser.add_argument('library_file', type=file)

    def handle(self, *args, **options):
        dataReader = csv.reader(options['library_file'], delimiter=',', quotechar='"')
        for prow in dataReader:
            error_log("LINE: %s" % str(prow))
            if prow[1] not in catcache:
                xxx = Category.objects.filter(code__exact=prow[1]).first()
                error_log("CAT: %s" % str(xxx))
                if xxx:
                    catcache[prow[1]] = xxx
                else:
                    error_log("CAT: %s NOT FOUND" % str(prow[1]))
                    continue

            category = catcache[prow[1]]
            title = ' '.join(prow[2].split())
            title = ', '.join(title.split(','))
            callno = ' '.join(prow[0].split())
            composer = ' '.join(prow[3].split())
            if not composer:
                composer = "--unknown--"
            arranger = ""
            iio = None
            aao = None
            ccc = None


            if category.code == 'M':
                timesig = prow[4]
                composer = ' '.join(prow[3].split())
                callno = callno + ("/%s" % title[:4].upper())
            elif category.code == 'So':
                instrument = prow[3].strip()
                composer = ' '.join(prow[4].split())
                iio = Instrument.objects.filter(name__iexact=instrument).first()
                if iio:
                    error_log("INSTRUMENT: %s" % iio.name)
                else:
                    error_log("NEW INSTRUMENT: %s" % instrument)
                    iiio = Instrument()
                    iiio.name = instrument
                    iiio.save()
                    iio = iiio
            else:
                if category.code == 'W':                    
                    arranger = ' '.join(prow[3].split())
                    composer = ' '.join(prow[4].split())
                else:
                    arranger = ' '.join(prow[4].split())
                    composer = ' '.join(prow[3].split())

                if arranger:
                    aaac = arranger.split(',')
                    aaas = arranger.split(' ')
                    given = ""
                    surname = ""
                    if len(aaac) > 1:
                        given = ' '.join(aaac[1].split()).strip('.')
                        surname = ' '.join(aaac[0].split()).strip('.')
                        error_log("CHECK COMMA ARRANGER: '%s', '%s'" % (surname, given))
                        aao = Author.objects.filter(surname__iexact=surname, given__iexact=given).first()
                    elif len(aaas) > 1:
                        given = ' '.join(aaas[0].split()).strip('.')
                        surname =  (" ".join(aaas[1:])).strip('.')
                        error_log("CHECK SPACE ARRANGER: '%s', '%s'" % (surname, given))
                        aao = Author.objects.filter(surname__iexact=surname, given__iexact=given).first()
                    else:
                        surname = ' '.join(aaac[0].split()).strip('.')
                        given = ""
                        error_log("CHECK SINGLE ARRANGER: '%s', '%s'" % (surname, given))
                        aao = Author.objects.filter(surname__iexact=surname).first()

                    if aao:
                        error_log("FOUND ARRANGER: %s" % str(aao))
                    else:
                        error_log("NEW ARRANGER: '%s', '%s'" % (surname, given))
                        na = Author()
                        na.surname = surname
                        na.given = given
                        na.save()
                        aao = na

            # print >>sys.stderr, "COMPOSER LINE: %s" % composer
            if not composer:
                composer = "--unknown--"

            if composer:
                cccomma = composer.split(',')
                ccspace = composer.split(' ')
                ccamp = composer.split('&')

                given = ""
                surname = ""

                if len(ccamp) > 1:
                    surname = ' '.join(composer.split()).strip('.')
                    error_log("CHECK AMPER COMPOSER: %s, %s" % (surname, given))
                    ccc = Author.objects.filter(surname__iexact=surname).first()
                elif len(cccomma) > 1:
                    given = ' '.join(cccomma[1].split()).strip('.')
                    surname = ' '.join(cccomma[0].split())
                    error_log("CHECK COMMA COMPOSER: %s, %s" % (surname, given))
                    ccc = Author.objects.filter(surname__iexact=surname, given__iexact=given).first()
                elif len(ccspace) > 1:
                    given = ' '.join(ccspace[0].split()).strip('.')
                    surname =  (" ".join(ccspace[1:])).strip()
                    error_log("CHECK SPACE COMPOSER: %s, %s" % (surname, given))
                    ccc = Author.objects.filter(surname__iexact=surname, given__iexact=given).first()
                else:
                    surname = ' '.join(cccomma[0].split()).strip('.')
                    error_log("CHECK SINGLE COMPOSER: %s, %s" % (surname, given))
                    ccc = Author.objects.filter(surname__iexact=surname).first()

                error_log("COMPOSER RESULT: %s" % str(ccc))

                if ccc:
                    error_log("FOUND COMPOSER: %s" % str(ccc))
                else:
                    error_log("NEW COMPOSER: %s" % composer)
                    na = Author()
                    na.surname = surname
                    na.given = given
                    na.save()
                    ccc = na



            if ccc:
                www = Entry.objects.filter(title__iexact=title, composer__exact=ccc, category__exact=category).first()
                lll = Entry.objects.filter(callno__exact=callno, category__exact=category).first()

                if not (www or lll):
                    try:
                        eee = Entry()
                        eee.title = title
                        eee.composer = ccc
                        eee.arranger = aao
                        eee.callno = callno
                        eee.category = category
                        eee.instrument = iio

                        eee.save()
                    except Exception as ee:
                        error_log("SAVE ENTRY FAILED: %s %s %s %s" % (str(ee), eee.title, eee.callno, eee.category))
                elif (www and lll):
                    if (www.pk != lll.pk):
                        error_log("CONFLICTING ENTRY RESULTS: (%s %s %s) T %s L %s" % (title, callno, category, str(www), str(lll)))
                    else:
                        error_log("MATCHING ENTRY RESULTS: (%s %s %s) T %s L %s" % (title, callno, category, str(www), str(lll)))
                else:
                    error_log("INCOMPLETE ENTRY RESULTS: (%s %s %s) T %s L %s" % (title, callno, category, str(www), str(lll)))
            else:
                error_log("MISSING COMPOSER: (%s %s %s)" % (title, callno, category))