from tinymce import models as tinymce_models
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.deletion import CASCADE, SET_NULL, PROTECT
from django.contrib.auth.models import User
from .utilx import error_log

from django.contrib.auth.models import User
import decimal

def get_full_name(self):
    if self.first_name:
        if self.last_name:
            return "%s %s" % (self.first_name, self.last_name)
        else:
            return self.first_name
    else:
        return self.username

User.add_to_class("__str__", get_full_name)

# a label consists of two numbers: physical-item . musical-item (starts at 0) - so a piece with two parts has 1234 and 1234.1
# the issue is that 1234.1 is not the same as 1234.10
# perhaps the way is to make 1234.1 into 1234.01

class LabelField(models.DecimalField):
    decimal_digits = 2
    max_digits = 8

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
#        vvv = decimal.Decimal(value.lstrip("0"))
        vvv = value
        error_log("LABEL: FROM DB %s" % str(vvv))
        return vvv.normalize()

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        error_log("LABEL: GET PREP %s" % str(value))
#        value = "00000000000" + value
#        return value[-self.max_length:]
        return value

    def to_python(self, value):
        value = super().to_python(value)
        #        vvv = decimal.Decimal(value.lstrip("0"))
        vvv = value
        error_log("LABEL: TO PYTHON %s" % str(vvv))
        return vvv.normalize()

class Source(models.Model):
    label = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return '%s' % self.label
    
    class Meta:
        ordering = ('label',)

class Material(models.Model):
    label = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return '%s' % self.label

class Completeness(models.Model):
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True,null=True)
    usable = models.BooleanField(default=False)

    def __str__(self):
        if self.usable:
            return '%s' % self.label
        else:
            return "%s (unusable)" % self.label

class Tonality(models.Model):
    from django.core.validators import MaxValueValidator, MinValueValidator
    MODE = (
        ('maj', 'Major'),
        ('min', 'Minor'),
        ('X', 'N/A')
    )
    ACCTYPE = (
        ('none', '-'),
        ('flat', 'flat'),
        ('sharp', 'sharp')
    )
    PITCH = (
        ('C','C'),('C#','C sharp'),
        ('D','D'),('Db','D flat'),
        ('E','E'),('Eb','E flat'),
        ('F','F'),('F#','F sharp'),
        ('G','G'),
        ('A','A'),('Ab','A flat'),
        ('B','B'),('Bb','B flat'),
        ('X','Not Defined'),
        ('Y','Ambiguous'),
        ('Z','Keyless')
    )

    pitch = models.CharField(max_length=2, choices=PITCH)
    mode = models.CharField(max_length=4, choices=MODE)
    accidentals = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(7)])
    acctype = models.CharField(max_length=5, choices=ACCTYPE,blank=False,null=False )

    def __str__(self):
        if self.pitch == 'X':
            return 'Not determined'
        elif self.pitch == 'Y':
            return 'Ambiguous'
        elif self.pitch == 'Z':
            return 'Non-specific/Keyless'
        else:
            return "%s %s (%d%s)" % (self.pitch, self.mode, self.accidentals, ("" if self.acctype == 'none' else " %s" % self.acctype))
    
    class Meta:
        ordering = ('acctype','accidentals')
        verbose_name = "Key"
        

    # key as for the transposing instrument - target is also a Tonality
    def transposed(self, target):
        if target.accidentals > 0:
            if target.acctype == 'flat':
                nacc = -self.accidentals + target.accidentals # for Bb: F (1f) -> G(1s) = -1 + 2 = 1
                atype = 'sharp' if nacc > 0 else ('flat' if nacc < 0 else 'none')
                return Tonality.objects.filter(mode=target.mode, accidentals=nacc, acctype=atype).first()
            elif target.acctype == 'sharp':
                nacc = self.accidentals - target.accidentals # for G: F (1f) -> C(0) = 1 - 1 = 0
                atype = 'sharp' if nacc > 0 else ('flat' if nacc < 0 else 'none')
                return Tonality.objects.filter(mode=target.mode, accidentals=nacc, acctype=atype).first()
        else:
            return self

        # concert key for the transposing instrument - target is also a Tonality
    def concert(self, target):
        if target.accidentals > 0:
            if target.acctype == 'sharp':
                nacc = -self.accidentals + target.accidentals # for G: C (0) -> G(1s) = 0 + 1 = 1
                atype = 'sharp' if nacc > 0 else ('flat' if nacc < 0 else 'none')
                return Tonality.objects.filter(mode=target.mode, accidentals=nacc, acctype=atype).first()
            elif target.acctype == 'flat':
                nacc = self.accidentals - target.accidentals # for Bb: G (1s) -> F(1f) = 1 - 2 = -1
                atype = 'sharp' if nacc > 0 else ('flat' if nacc < 0 else 'none')
                return Tonality.objects.filter(mode=target.mode, accidentals=nacc, acctype=atype).first()
        else:
            return self


class Ensemble(models.Model):
    name = models.CharField(max_length=32)
    
    def __str__(self):
        return self.name
    
class EntryManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        
        return qs.select_related('category','genre')

class Entry(models.Model):
    title = models.CharField(max_length=200)
#    callno = LabelField(max_length=12, verbose_name="label", db_column="labelnum")
    callno = LabelField(max_length=12, max_digits=10, decimal_places=2, verbose_name="label", db_column="labelnum")
    oldpagecount = models.IntegerField(blank=True, null=True, verbose_name="Page count", help_text="for solo cornet")
    duration = models.CharField(max_length=8, default="0:0", help_text="approx duration - MM:SS - leave as 0:0 when not known")
    composer = models.ForeignKey('Author', blank=True, null=True, related_name="compositions", on_delete=CASCADE)
    arranger = models.ForeignKey('Author', blank=True, null=True, related_name="arrangements", on_delete=CASCADE)
    category = models.ForeignKey('Category', verbose_name='Shelving Category', on_delete=CASCADE)
    genre = models.ForeignKey('Genre', verbose_name='Type/Genre of Work', blank=True, null=True, on_delete=SET_NULL)
    key = models.ForeignKey('Tonality', verbose_name='Solo Cornet Key of Work', blank=True, null=True, on_delete=CASCADE)
    ensemble = models.ForeignKey('Ensemble', on_delete=PROTECT)
    publisher = models.ForeignKey('Publisher', blank=True, null=True, related_name="pubyears", on_delete=CASCADE)
    pubyear = models.IntegerField(verbose_name='Year of edition', blank=True, null=True)
    estdecade = models.IntegerField(verbose_name='Est. Decade', help_text="If exact year not known", blank=True, null=True)
    pubname = models.ForeignKey('Publication', verbose_name='Publication', blank=True, null=True, related_name="publications", on_delete=CASCADE)
    pubissue = models.CharField(max_length=24,verbose_name='Vol/Issue', blank=True, null=True)
    saleable = models.BooleanField(default=False, verbose_name='Ready for sale')
    fee = models.DecimalField(blank=True, null=True, max_digits=6, decimal_places=2, verbose_name='Fee (AUD)')
    platecode = models.CharField(max_length=12, blank=True, null=True)
    comments = models.TextField(blank=True, null=True, verbose_name='Private comments')
    backpage = models.TextField(verbose_name='Back page comments (e.g. ads)', blank=True, null=True)
    perfnotes = models.TextField(verbose_name='Performance notes', blank=True, null=True)
    added = models.DateField(verbose_name='Date added', auto_now=True)
    instrument = models.ForeignKey("Instrument", blank=True, null=True, on_delete=CASCADE)
    #media = models.CharField(max_length=256, blank=True, null=True)
    oldmedia = models.FileField(upload_to='', max_length=256, blank=True, null=True)
    source = models.ForeignKey("Source", blank=True, null=True, related_name="+", on_delete=SET_NULL)
    provider = models.ForeignKey('Author', blank=True, null=True, related_name="donations", on_delete=CASCADE)
#    digitised = models.BooleanField(default=False)
    material = models.ForeignKey('Material', blank=True, null=True, related_name="+", on_delete=CASCADE)
    condition = models.ForeignKey('Condition', blank=True, null=True, related_name="+", on_delete=CASCADE)
#    incomplete = models.BooleanField(default=False)
    # allow nulls initially
    completeness = models.ForeignKey('Completeness', blank=True, null=True, related_name="+", on_delete=SET_NULL)
    duplicate = models.BooleanField(default=False, verbose_name='Already in library?')
    
    objects = EntryManager()

    class Meta:
        unique_together = ('callno', 'category')
        verbose_name_plural = "Entries"
        ordering = ['title','composer__surname']
        permissions = [
            ("march_only", "Can only see marches.")
        ]

    def __str__(self):
        return '%s (%s,%s)' % (self.title, self.category.code, self.callno)
    
    # main check: if 'saleable' then certain fields must be set
    
#    def clean(self):
#        salefields = ('title', 'composer','publisher','media','genre','duration')
#        return
    
    @property
    def media(self):
        item = self.related_media.filter(asthumb=True).first()
        if item:
            return item.mfile
        else:
            return None
        
    @property
    def pagecount(self):
        item = self.related_media.filter(asthumb=True).first()
        if item:
            return item.pagecount
        else:
            return None
    
    @property
    def incomplete(self):        
        return not (self.completeness and self.completeness.usable)
    
class LibraryPersona(models.Model):
    label = models.CharField(max_length=128, unique=True)
    #TODO: add ACL-type attributes
    
    def __str__(self):
        return self.label
    
class EntryPurpose(models.Model):
    label = models.CharField(max_length=128, unique=True)
    
    def __str__(self):
        return self.label
    
class EntryMediaManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        
        return qs.select_related('purpose','visibility')
    
class EntryMedia(models.Model):
    MTPDF = "PDF"
    MTIMAGE = "IMAGE"
    MTVIDEO = "VIDEO"
    MTAUDIO = "AUDIO"
    MTOTHER = "OTHER"
    MEDIATYPES = (
        (MTPDF, "PDF"),
        (MTIMAGE, "Image"),
        (MTVIDEO, "Video"),
        (MTAUDIO, "Audio"),
        (MTOTHER, "Other/Unknown")
    )
    
    entry = models.ForeignKey(Entry, related_name='related_media', on_delete=CASCADE)
    mfile = models.FileField(upload_to='', max_length=256, verbose_name='Filename')
    mtype = models.CharField(max_length=8, choices=MEDIATYPES, default="OTHER", verbose_name="Media Type")
    purpose = models.ForeignKey(EntryPurpose, on_delete=PROTECT)
    visibility = models.ForeignKey(LibraryPersona, on_delete=PROTECT, verbose_name="Visible to")
    pagecount = models.IntegerField(blank=True, null=True, verbose_name="Page count")
    asthumb = models.BooleanField(default=False, verbose_name='Use for Advert')
    comment = models.CharField(max_length=128, blank=True, null=True)
    objects = EntryMediaManager()
    
#    def clean(self):
#        nthumbs = self.entry.related_media.filter(asthumb=True).count()
#        if False and nthumbs > 1:
#            raise ValidationError('Only one media item can be for an - %d found' % (nthumbs,))
#        return
    
    class Meta:
        verbose_name = "Related file"
        verbose_name_plural = "Related files"
        
class PublicationManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        
        return qs.select_related('publisher')
    

class Publication(models.Model):
    name = models.CharField(max_length=128)
    publisher = models.ForeignKey('Publisher', blank=True, null=True, related_name="publications", on_delete=CASCADE)
    comments = models.TextField(blank=True, null=True)
    objects = PublicationManager()

    class Meta:
        unique_together = ('name', 'publisher')
        ordering = ['name',]

    def __str__(self):
        if self.publisher:
            return '%s (%s)' % (self.name, self.publisher.name)
        else:
            return '%s ()' % self.name
        
class PublisherManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        
        return qs.select_related('country')

class Publisher(models.Model):
    name = models.CharField(max_length=128)
    country = models.ForeignKey('Country', blank=True, null=True, related_name="publishers", on_delete=CASCADE)
    comments = models.TextField(blank=True, null=True)
    objects = PublisherManager()

    class Meta:
        unique_together = ('name', 'country')
        ordering = ['name',]

    def __str__(self):
        if self.country:
            return '%s (%s)' % (self.name, self.country)
        else:
            return '%s ()' % self.name

class SeeAlso(models.Model):
    source_entry = models.ForeignKey(Entry, related_name='related_entries', on_delete=CASCADE)
    entry = models.ForeignKey(Entry, related_name='cited_by', blank=True, null=True, on_delete=CASCADE)
    purpose = models.ForeignKey(EntryPurpose, blank=True, null=True, on_delete=PROTECT)
#    url = models.URLField(blank=True, null=True)
    comment = models.CharField(max_length=256, blank=True, null=True)

#    def clean(self):
#        error_log("SEE_ALSO MODEL CLEAN %s" % str(self))
#        if not self.entry and not self.url:  # This will check for None or Empty
#            raise ValidationError({'entry': 'At least one of field1 or field2 must have a value.'})
#        if self.entry and self.url:  # This will check for None or Empty
#            raise ValidationError({'entry': 'Set either entry or URL but not both.'})

    def __str__(self):
        return str(self.entry)
    
    class Meta:
        verbose_name = "Related Library Entry"
        verbose_name_plural = "Related Library Entries"
        
class WebLink(models.Model):
    entry = models.ForeignKey(Entry, related_name='weblinks', on_delete=CASCADE)
    url = models.URLField()
    purpose = models.ForeignKey(EntryPurpose, blank=True, null=True, on_delete=PROTECT)
    comment = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return str(self.url)
    
    class Meta:
        verbose_name = "Web Link"



class Author(models.Model):
    surname = models.CharField(max_length=32)
    given = models.CharField(max_length=48, blank=True, null=True)
    bornyear = models.IntegerField(blank=True, null=True, verbose_name='Year of Birth')
    diedyear = models.IntegerField(blank=True, null=True, verbose_name='Year of Death')
    country = models.ForeignKey('Country', blank=True, null=True, related_name="authors", on_delete=CASCADE)
    realname = models.ForeignKey('Author', blank=True, null=True, related_name="pennames", on_delete=CASCADE)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('surname', 'given')
        ordering = ['surname', 'given']
        
    @classmethod
    def find(cls, name):
        # assume surname, firstname in list
        if len(name) == 0:
            return None
        if len(name) >= 2 and name[1]:
            author = cls.objects.filter(surname__iexact=name[0], given__iexact=name[1]).first()
        else:
            author = cls.objects.filter(surname__iexact=name[0]).first()
        return author

    def __str__(self):
        if self.given:
            return '%s, %s' % (self.surname, self.given)
        else:
            return '%s' % self.surname

class Country(models.Model):
    name = models.CharField(max_length=48)
    isocode = models.CharField(max_length=3)

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ['name']

    def __str__(self):
        return '%s (%s)' % (self.name, self.isocode)

class Condition(models.Model):
    name = models.CharField(max_length=48)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return '%s' % (self.name)

class Instrument(models.Model):
    name = models.CharField(max_length=48)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return '%s' % (self.name)

class Category(models.Model):
    label = models.CharField(max_length=32)
    code = models.CharField(max_length=2)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['label']

    def __str__(self):
        return '%s (%s)' % (self.label, self.code)

class Genre(models.Model):
    label = models.CharField(max_length=32)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Genres"
        ordering = ['label']

    def __str__(self):
        return '%s' % (self.label)


class Program(models.Model):
    performance_date = models.DateField()
    title = models.CharField(max_length=200, verbose_name='Title/Theme', default='Title of Performance')
    venue = models.CharField(max_length=200, default='Venue of Performance')
    comments = models.TextField(blank=True, null=True)


    def __str__(self):
        return '%s: "%s" at %s' % (str(self.performance_date), str(self.title), str(self.venue))
    
        
class ProgramItem(models.Model):
    program = models.ForeignKey(Program, related_name='items', on_delete=CASCADE)
    item = models.ForeignKey(Entry, blank=True, null=True, verbose_name="Library item", related_name='performances', on_delete=CASCADE)
    extitem = models.CharField(max_length=200, blank=True, null=True, verbose_name="External item", help_text="New or externally sourced item")
    comments = models.TextField(blank=True, null=True)
    
    def __str__(self):
        if self.item:
            return '%s' % (self.item.title)
        else:
            return self.extitem
    
    def clean(self):
        if not (self.item or self.extitem):
            raise ValidationError("Specify at least an library item or an external item")
        

class AssetType(models.Model):
    label = models.CharField(max_length=128)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return '%s' % (self.label)

class AssetCondition(models.Model):
    label = models.CharField(max_length=128)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return '%s' % (self.label)

class AssetMaker(models.Model):
    label = models.CharField(max_length=128)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return '%s' % (self.label)

class AssetModel(models.Model):
    label = models.CharField(max_length=128)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return '%s' % (self.label)

class Asset(models.Model):
    asset_type = models.ForeignKey(AssetType, related_name='assets', on_delete=CASCADE)
    year_of_acquisition = models.IntegerField(blank=True, null=True)
    asset_condition = models.ForeignKey(AssetCondition, related_name='assets', on_delete=CASCADE)
    allocated = models.BooleanField(verbose_name="Allocated/In Use", default=False)
    identifier = models.CharField(max_length=256, help_text="Serial no or other unique")
    description = models.TextField(blank=True, null=True)
    manufacturer = models.ForeignKey(AssetMaker, related_name='assets', on_delete=CASCADE)
    model = models.ForeignKey(AssetModel, related_name='assets', blank=True, null=True, on_delete=CASCADE)
    location = models.TextField(blank=True, null=True, help_text="Name/address of borrower or place")
    owner = models.CharField(max_length=256, blank=True, null=True, help_text="Actual owner if not Oakleigh Brass")
    last_maintained = models.DateField(blank=True, null=True)

    def __str__(self):
        return '%s - %s: %s' % (self.asset_type, self.manufacturer, self.model)
    
class TaskStatus(models.Model):
    description = models.CharField(max_length=64)
    
    def __str__(self):
        return self.description
    
class Task(models.Model):
    summary = models.CharField(max_length=256)
    description = models.TextField(blank=True, null=True)
    status = models.ForeignKey(TaskStatus, on_delete=CASCADE)
    person = models.ForeignKey(User, related_name="tasks", verbose_name="Internal person", blank=True, null=True, on_delete=SET_NULL)
    extperson = models.CharField(max_length=256, verbose_name="External person", blank=True, null=True)
    create_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(blank=True, null=True)
    completion_date = models.DateField(blank=True, null=True)
    
    def clean(self):
        if not (self.person or self.extperson):
            raise ValidationError("Specify at least an internal or external person.")
    
    
    def __str__(self):
        return "%s [%s]" % (self.summary, str(self.create_date))
    
class TaskNote(models.Model):
    task = models.ForeignKey(Task, related_name="notes", on_delete=CASCADE)
    date = models.DateField(auto_now_add=True)
    description = models.TextField()
    
class TaskItem(models.Model):
    task = models.ForeignKey(Task, related_name="items", on_delete=CASCADE)
    entry = models.ForeignKey(Entry, related_name="tasks", blank=True, null=True, on_delete=SET_NULL)
    asset = models.ForeignKey(Asset, related_name="tasks", blank=True, null=True, on_delete=SET_NULL)
    note = models.TextField(blank=True, null=True)
    
    def clean(self):
        if not (self.entry or self.asset):
            raise ValidationError("Specify at least an entry and/or asset")

        
    
class FolderItem(models.Model):
    folder = models.ForeignKey('Folder', related_name="slots", on_delete=CASCADE)
    entry = models.ForeignKey(Entry, related_name="folders", blank=True, null=True, on_delete=SET_NULL)
    comment = models.TextField(blank=True, null=True)
    version = models.CharField(max_length=5, blank=True, null=True)
    position = models.IntegerField()

    def clean(self):
        if not (self.entry or self.comment):
            raise ValidationError("Specify at least an entry or a comment.")
        
    def item(self):
        if self.entry:
            return "%s" % str(self.entry.title)
        else:
            return "%s" % self.comment
    
    def __str__(self):
        if self.entry:
            return "E %s (%s) " % (str(self.entry.title), str(self.position))
        else:
            return "C %s (%s) " % (self.comment, str(self.position))
        
class FolderManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        fiqs = FolderItem.objects.select_related('entry','entry__category')
            
            # it's really important to use the to_attr parameter, so that we get a list of the companies without incurring further DB hits

#            family_preset = Prefetch('entity__family', queryset=pfqs, to_attr='companies')
        qqs = qs.prefetch_related('slots').prefetch_related(models.Prefetch('slots', queryset=fiqs.order_by('entry__label'), to_attr='byname')).prefetch_related(models.Prefetch('slots', queryset=fiqs.order_by('position'), to_attr='byslot'))
        return qqs
        
class Folder(models.Model):
    label = models.CharField(max_length=256)
    slot_count = models.IntegerField(default=35)
    issue_date = models.DateField()
    sidebar = tinymce_models.HTMLField(blank=True, null=True, help_text="Text to annotate the index.")
    objects = FolderManager()
    
    def __str__(self):
        return "%s (%d)" % (self.label, self.slot_count)
    
    @property
    def alphabetic(self):
#        return self.slots.order_by('entry__label')
        return self.byname
    
    @property
    def numeric(self):
        allslots = {}
        
        for ss in range(0, self.slot_count):
            # prefill available slots
            error_log("PREFILL '%s'" % str(ss+1))
            allslots[str(ss+1)] = None
            
        for sss in self.byslot:
            error_log("REFILL '%s'" % str(sss.position))
            allslots[str(sss.position)] = sss
            
        error_log("SLOTS '%s'" % str(allslots))
        return allslots
    
    class Meta:
        verbose_name = "Music Folder"
        ordering = ['label']
    
    

    
