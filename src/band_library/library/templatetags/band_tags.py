import os
from imagekit import ImageSpec, register
from imagekit.processors import ResizeToFill
from django import template

register = template.Library()
basedir = '/Users/david/src/BandLibrary'
mediadir = os.path.join(basedir, 'media')
cachedir = os.path.join(basedir, 'mediacache')

class Incipit(ImageSpec):
    processors = [ResizeToFill(100, 50)]
    format = 'JPEG'
    options = {'quality': 60}
    
@register.filter(name='incipit')
def makethumb(value):
    ffc = open(os.path.join(mediadir, value + ".jpg"), "rb")
    if not ffc:
        fff = open(os.path.join(mediadir, value), "rb")
    iii = Incipit(source=fff)    
    return iii.generate()

@register.filter(name='totitle')
def maketitle(value):
    result = ' '.join(elem.capitalize() for elem in value.split())
    return result
