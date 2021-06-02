import argparse
import datetime
import csv

import os
import sys
import subprocess
from operator import attrgetter, itemgetter
from shutil import copyfile

# config items

TEMPLATE = "%(title)s - %(part)s%(suffix)s"
SOUNDS = {'target': '1 Play and Listen'}
PARTS = [
{ 'name': 'Soprano Cornet', 'num': 1, 'target': '2 Soprano'},
{ 'name': 'Solo Cornet', 'num': 4, 'target': '3 Solo Cornet'},
{ 'name': 'Repiano Cornet', 'num': 1, 'target': '4 Repiano'},
{ 'name': '2nd Cornet', 'num': 3, 'target': '5 2nd Cornet'},
{ 'name': '3rd Cornet', 'num': 3, 'target': '6 3rd Cornet'},
{ 'name': 'Flugelhorn', 'num': 1, 'target': '7 Flugel'},
{ 'name': 'Solo Horn', 'num': 2, 'target': '8 Solo Horn'},
{ 'name': '1st Horn', 'num': 2, 'target': '9 1st Horn'},
{ 'name': '2nd Horn', 'num': 2, 'target': '10 2nd Horn'},
{ 'name': '1st Baritone', 'num': 1, 'target': '11 1st Baritone'},
{ 'name': '2nd Baritone', 'num': 1, 'target': '12 2nd Baritone'},
{ 'name': '1st Trombone', 'num': 1, 'target': '13 1st Trombone'},
{ 'name': '2nd Trombone', 'num': 1, 'target': '14 2nd Trombone'},
{ 'name': 'Bass Trombone', 'num': 1, 'target': '15 Bass Trombone'},
{ 'name': 'Euphonium', 'num': 2, 'target': '16 Euphonium'},
{ 'name': 'Eb Bass', 'num': 3, 'target': '17 Eb Bass'},
{ 'name': 'Bb Bass', 'num': 2, 'target': '18 Bb Bass'},
{ 'name': 'Percussion', 'num': 2, 'target': '19 Percussion'},
]

suffix = ".pdf"

def logit(msg, myfile=sys.stderr):
    myfile.write("%s\n" % msg)
    myfile.flush()

parser = argparse.ArgumentParser(description="Compare ADB company balance date to BR balance date")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--csv', help="Process CSV file (8 cols - ignore, srcdir, srcitem, dstdir, dstitem, version, audio-src, audio-item)", nargs=1)
group.add_argument('--item', help="Process single item: srcdir srcitem dstdir dstitem version", nargs=5)
parser.add_argument('--audio', help="Process audio for single item (ignored for CSV): srcdir srcitem", nargs=2)
parser.add_argument('--defv', help="Version number for sources without one", nargs=1, default='0.1')

parser.add_argument('--list', help='list pieces', action='store_true')
parser.add_argument('--test', help='dry run', action='store_true')
parser.add_argument('--dbg', help='debug', action='store_true')
parser.add_argument('--verbose', help='be chatty about things', action='store_true')

args = parser.parse_args()

def report(msg, myfile=sys.stderr):
    myfile.write("%s\n" % msg)
    myfile.flush()

items = []

if args.csv:
    if args.dbg:
        report("CSV %s" % str(args.csv))
    filename = args.csv[0]
    reader = csv.reader(open(filename, "r"))
    next(reader) # skip first row
    try:
        for row in reader:
            if row[0] != "":
                report("Ignoring %s" % row[2])
                continue

            newitem = {
                'srcdir': row[1],
                'srcitem': row[2],
                'dstdir': row[3],
                'dstitem': row[4],
                'version': row[5]
            }

            if len(row) == 8 and row[6] and row[7]:
                newitem['asource'] = row[6]
                newitem['aitem'] = row[7]

            items.append(newitem)

    except csv.Error as e:
        sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))
else:
    if args.dbg:
        report("ITEM %s" % str(args.item))
    items.append(
        {
            'srcdir': args.item[0],
            'srcitem': args.item[1],
            'dstdir': args.item[2],
            'dstitem': args.item[3],
            'version': args.item[4]
        }
    )

    if args.audio:
        items[0]['asource'] = args.audio[0]
        items[0]['aitem'] = args.audio[1]

if args.dbg:
    report("%s" % str(items))

if len(items) == 0:
    report("nothing to do")
    sys.exit(1)

# sys.exit(1)

allfiles = []
usenew = False

errors = 0
# check parts against given version
for item in items:
    # item is a dict
    for part in PARTS:
        if item['version']:
            if item['version'] == "$":
                suffix = ".pdf"
            else:
                suffix = "-%s.pdf" % item['version']
            dsuffix = suffix
        else:
            suffix = ".pdf"
            dsuffix = "-%s.pdf" % args.defv[0]

        srcfile = TEMPLATE % { 'title': item['srcitem'], 'part': part['name'], 'suffix': suffix}
        dstfile = TEMPLATE % { 'title': item['dstitem'], 'part': part['name'], 'suffix': dsuffix}

        srcpath = "%s/%s" % (item['srcdir'], srcfile)

        dstdir = "%s/%s" % (item['dstdir'], part['target'])
        dstpath = "%s/%s" % (dstdir, dstfile)

        if args.dbg:
            report("Seek part: %s" % srcpath)
            report("Target path: %s" % dstpath)

        if not os.path.exists(dstdir):
            report("Target %s not found" % dstdir)
            errors += 1

        if not os.path.exists(srcpath):
            report("Item %s part %s not found (%s)" % (item['srcitem'], part['name'], srcpath))
            errors += 1

        item[part['name']] = {
            'srcpath': srcpath,
            'dstpath': dstpath
        }

    if item.get('asource', None):
        audiofile = '%s/%s' % (item['asource'], item['aitem'])

        if not os.path.exists(audiofile):
            report("Audio file %s not found" % audiofile)
            errors += 1

        atype = os.path.splitext(audiofile)[1]
        if item['version']:
            if item['version'] == "$":
                asuffix = atype
            else:
                asuffix = "-%s%s" % (item['version'], atype)
            adsuffix = asuffix
        else:
            asuffix = atype
            adsuffix = "-%s%s" % (args.defv[0], atype)

        adest = "%s/%s/%s%s" % (item['dstdir'], SOUNDS['target'], item['dstitem'], adsuffix)

        item['audiofile'] = audiofile
        item['audiodest'] = adest


if errors:
    sys.exit(1)

for item in items:
    # item is a dict
    for part in PARTS:
        if not os.path.exists(item[part['name']]['dstpath']) or os.path.getmtime(item[part['name']]['srcpath']) > os.path.getmtime(item[part['name']]['dstpath']):
            if args.test:
                report("Copy '%s' to '%s' (dry run)" % (item[part['name']]['srcpath'], item[part['name']]['dstpath']))
            else:
                report("Copy '%s' to '%s'" % (item[part['name']]['srcpath'], item[part['name']]['dstpath']))
                copyfile(item[part['name']]['srcpath'], item[part['name']]['dstpath'])
        elif args.verbose:
            report("Dest '%s' is up to date" % item[part['name']]['dstpath'])

    if item.get('audiofile', None):

        if not os.path.exists(item['audiodest']) or os.path.getmtime(item['audiofile']) > os.path.getmtime(item['audiodest']):
            if args.test:
                report("Copy '%s' to '%s' (dry run)" % (item['audiofile'], item['audiodest']))
            else:
                report("Copy '%s' to '%s'" % (item['audiofile'], item['audiodest']))
                copyfile(item['audiofile'], item['audiodest'])
        elif args.verbose:
            report("Dest '%s' is up to date" % item['audiodest'])


