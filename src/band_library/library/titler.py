import re
EXCLUSIONS = ('the', 'a', 'an', 'by', 'with', 'from')
EXCLUSIONSRE = [r'^the$', r'^a$', r'^an$', r'^by$', r'^with$', r'^from$', r'^of$', r'^\d+']

def matches_any(text, patterns):
    return any(re.search(p, text) for p in patterns)


def titlecase(s):
    # remove trailing stuff after ' - ' (non greedy)
    tricky1re = re.compile(r'(.*), (\ba\b|\bthe\b)(.*)', flags=re.I) # separate article
    tricky2re = re.compile(r'(.*?) - .*', flags=re.I) # comment in title
    s0 = tricky1re.sub(r"\2 \1\3", s)
    s1 = tricky2re.sub(r"\1", s0)
    s2 = re.sub(
        r"[A-Za-z0-9]+('[A-Za-z]+)?",
        lambda word: word.group(0).lower() if matches_any(word.group(0).lower(), EXCLUSIONSRE) else word.group(0).capitalize(),
        s1)
    # return s2
    # print("S2 %s" % s2)
    return s2[0].upper() + s2[1:]

xxx = 'the kevin\'s adagio From the "orange jiuce" thing - no links - or files'
yyy = '2nd of kevin\'s adagio from the "orange jiuce" thing - no links - or files'

print(xxx.title())
print(titlecase(xxx))

print(yyy.title())
print(titlecase(yyy))
