import re
EXCLUSIONS = ('the', 'a', 'an', 'by', 'with', 'from')
def titlecase(s):
    # remove trailing stuff after ' - ' (non greedy)
    tricky2re = re.compile(r'(.*?) - .*', flags=re.I) # comment in title
    s1 = tricky2re.sub(r"\1", s)
    s2 = re.sub(
        r"[A-Za-z]+('[A-Za-z]+)?",
        lambda word: word.group(0) if word.group().lower() in EXCLUSIONS else word.group(0).capitalize(),
        s1)
    return s2[0].upper() + s2[1:]
        
        
xxx = 'the kevin\'s adagio from the "orange jiuce" thing - no links - or files'

print(xxx.title())
print(titlecase(xxx))
