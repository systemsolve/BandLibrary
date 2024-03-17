import sys
import os
import datetime
import subprocess
from django.http import FileResponse
from django.conf import settings

cachedir = settings.BL_CACHEDIR
mediadir = settings.BL_MEDIADIR

def error_log(msg):
    print(msg, file=sys.stderr)
    
def makeimage(fname, res, prefix):
    target = prefix + fname
    try:
#        error_log("open %s" % os.path.join(cachedir, target + ".jpg"))
        ffc = open(os.path.join(cachedir, target + ".jpg"), "rb")
    except:
        error_log("convert %s" % os.path.join(mediadir, fname))
        command = "pdftoppm -singlefile %s -jpeg \"%s\" \"%s\"" % (res, os.path.join(mediadir, fname), os.path.join(cachedir, target))
        error_log("command %s" % command)
        subprocess.call(command, shell=True)
        ffc = open(os.path.join(cachedir, target + ".jpg"), "rb")

    response = FileResponse(ffc, content_type="image/jpeg", charset='C')
    response['Cache-Control'] = "public"

    modtime = os.path.getmtime(os.path.join(cachedir, target + ".jpg"))
    response['Last-Modified'] = datetime.datetime.utcfromtimestamp(modtime).strftime("%a, %d %b %y %H:%M:%S GMT")
    return response

def makeimage2(fname, res, prefix):
    target = prefix + fname
    try:
#        error_log("open %s" % os.path.join(cachedir, target + ".jpg"))
        ffc = open(os.path.join(cachedir, target + ".jpg"), "rb")
    except:
        error_log("convert %s" % os.path.join(mediadir, fname))
        command = "convert %s -jpeg \"%s\" \"%s\"" % (res, os.path.join(mediadir, fname), os.path.join(cachedir, target))
        error_log("command %s" % command)
        subprocess.call(command, shell=True)
        ffc = open(os.path.join(cachedir, target + ".jpg"), "rb")

    response = FileResponse(ffc, content_type="image/jpeg", charset='C')
    response['Cache-Control'] = "public"

    modtime = os.path.getmtime(os.path.join(cachedir, target + ".jpg"))
    response['Last-Modified'] = datetime.datetime.utcfromtimestamp(modtime).strftime("%a, %d %b %y %H:%M:%S GMT")
    return response
