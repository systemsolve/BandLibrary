import os, re
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

EXCLUSIONS = ('the', 'a', 'an', 'by', 'with', 'from', 'of', 'to', 'and')

@register.filter(name='totitle')
def titlecase(s):
    # remove trailing stuff after ' - ' (non greedy)
    tricky1re = re.compile(r'(.*), (a|the)(.*)', flags=re.I) # separate article
    tricky2re = re.compile(r'(.*?) - .*', flags=re.I) # comment in title
    s0 = tricky1re.sub(r"\2 \1\3", s)
    s1 = tricky2re.sub(r"\1", s0)
    s2 = re.sub(
        r"[A-Za-z]+('[A-Za-z]+)?",
        lambda word: word.group(0) if word.group().lower() in EXCLUSIONS else word.group(0).capitalize(),
        s1)
    return s2[0].upper() + s2[1:]

def xxmaketitle(value):
    tricky1re = re.compile(r'(.*), (a|the)(.*)', flags=re.I) # separate article
    tricky2re = re.compile(r'(.*) - .*', flags=re.I) # comment in title
    
    value1 = tricky1re.sub(r"\2 \1\3", value)
    value2 = tricky2re.sub(r"\1", value1)
        
    
    result = ' '.join(elem.capitalize() for elem in value2.split())
    return result
