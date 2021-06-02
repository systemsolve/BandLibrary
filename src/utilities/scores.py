import os, sys, subprocess

def report(msg):
	print(msg, file=sys.stderr)

VERSION = 0.1
TITLE = "fleurs"
TEMPLATE = "%(title)s - %(part)s%(suffix)s" 
PARTS = [
{ 'name': 'Soprano Cornet', 'num': 1},
{ 'name': 'Solo Cornet', 'num': 4},
{ 'name': 'Repiano Cornet', 'num': 1},
{ 'name': '2nd Cornet', 'num': 3},
{ 'name': '3rd Cornet', 'num': 3},
{ 'name': 'Flugelhorn', 'num': 1},
{ 'name': 'Solo Horn', 'num': 2},
{ 'name': '1st Horn', 'num': 2},
{ 'name': '2nd Horn', 'num': 2},
{ 'name': '1st Baritone', 'num': 1},
{ 'name': '2nd Baritone', 'num': 1},
{ 'name': '1st Trombone', 'num': 1},
{ 'name': '2nd Trombone', 'num': 1},
{ 'name': 'Bass Trombone', 'num': 1},
{ 'name': 'Euphonium', 'num': 2},
{ 'name': 'Eb Bass', 'num': 3},
{ 'name': 'Bb Bass', 'num': 2},
{ 'name': 'Percussion', 'num': 2},
]

SCORES = [
{ 'name': 'cover', 'num': 1, 'norename': True},
{ 'name': 'Score', 'num': 1},
]

vsuffix = "-%s.pdf" % VERSION
suffix = ".pdf"

allfiles = []
usenew = False

errors = 0
# check parts against given version
for part in PARTS:
	file = TEMPLATE % { 'title': TITLE, 'part': part['name'], 'suffix': suffix}
	newfile = TEMPLATE % { 'title': TITLE, 'part': part['name'], 'suffix': vsuffix}
	if not (os.path.exists(newfile) or os.path.exists(file)):
		report("Part %s not found" % part)
		errors += 1

for part in SCORES:
	file = TEMPLATE % { 'title': TITLE, 'part': part['name'], 'suffix': suffix}
	newfile = TEMPLATE % { 'title': TITLE, 'part': part['name'], 'suffix': vsuffix}
	if not (os.path.exists(newfile) or os.path.exists(file)):
		report("Score file %s not found" % part)
		errors += 1

if errors:
	sys.exit(1)

masters = ['pdfjoin', '-o', "%s-master-%s.pdf" % (TITLE, VERSION) ]
fullset = ['pdfjoin', '-o', "%s-full-%s.pdf" % (TITLE, VERSION) ]
scoreset = ['pdfjoin', '--rotateoversize', 'false', '-o', "%s-fullscore-%s.pdf" % (TITLE, VERSION) ]

for part in PARTS:
	file = TEMPLATE % { 'title': TITLE, 'part': part['name'], 'suffix': ".pdf"}
	newfile = TEMPLATE % { 'title': TITLE, 'part': part['name'], 'suffix': vsuffix}
	if not os.path.exists(newfile):
		report("Rename '%s' to '%s'" % (file, newfile))
		os.rename(file, newfile)
	elif os.path.exists(file) and os.path.getmtime(file) > os.path.getmtime(newfile):
		report("Update '%s' to '%s'" % (file, newfile))
		os.rename(file, newfile)
	else:
		report("OK '%s'" % newfile)

	masters.append(newfile)
	for nn in range(part['num']):
		fullset.append(newfile)

for part in SCORES:
	file = TEMPLATE % { 'title': TITLE, 'part': part['name'], 'suffix': ".pdf"}
	newfile = TEMPLATE % { 'title': TITLE, 'part': part['name'], 'suffix': vsuffix}
	if part.get('norename', False):
		newfile = file
		report("NORENAME '%s'" % newfile)
	elif not os.path.exists(newfile):
		report("Rename '%s' to '%s'" % (file, newfile))
		os.rename(file, newfile)
	elif os.path.exists(file) and os.path.getmtime(file) > os.path.getmtime(newfile):
		report("Update '%s' to '%s'" % (file, newfile))
		os.rename(file, newfile)
	else:
		report("OK '%s'" % newfile)

	scoreset.append(newfile)

report("MASTER SET")
subprocess.run(masters)
report("FULL SET")
subprocess.run(fullset)
report("SCORE SET")
subprocess.run(scoreset)
