
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.deletion import CASCADE, SET_NULL
from django.contrib.auth.models import User
from .utilx import error_log

from django.contrib.auth.models import User

def get_full_name(self):
    if self.first_name:
        if self.last_name:
            return "%s %s" % (self.first_name, self.last_name)
        else:
            return self.first_name
    else:
        return self.username

User.add_to_class("__str__", get_full_name)

class LabelField(models.CharField):

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        return value.lstrip("0")

    def get_prep_value(self, value):
        value = super(LabelField, self).get_prep_value(value)
        value = "00000000000" + value
        return value[-self.max_length:]

    def to_python(self, value):
        value = super(LabelField, self).to_python(value)
        return value.lstrip("0")

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





class Entry(models.Model):
    title = models.CharField(max_length=200)
    callno = LabelField(max_length=12, verbose_name="label", db_column="label")
    pagecount = models.IntegerField(blank=True, null=True, verbose_name="Page count", help_text="for solo cornet")
    duration = models.CharField(max_length=8, default="0:0", help_text="approx duration - MM:SS - leave as 0:0 when not known")
    composer = models.ForeignKey('Author', blank=True, null=True, related_name="compositions", on_delete=CASCADE)
    arranger = models.ForeignKey('Author', blank=True, null=True, related_name="arrangements", on_delete=CASCADE)
    category = models.ForeignKey('Category', verbose_name='Shelving Category', on_delete=CASCADE)
    genre = models.ForeignKey('Genre', verbose_name='Type/Genre of Work', blank=True, null=True, on_delete=SET_NULL)
    key = models.ForeignKey('Tonality', verbose_name='Solo Cornet Key of Work', blank=True, null=True, on_delete=CASCADE)
    publisher = models.ForeignKey('Publisher', blank=True, null=True, related_name="pubyears", on_delete=CASCADE)
    pubyear = models.IntegerField(verbose_name='Year of edition', blank=True, null=True)
    estdecade = models.IntegerField(verbose_name='Est. Decade', help_text="If exact year not known", blank=True, null=True)
    pubname = models.ForeignKey('Publication', verbose_name='Publication', blank=True, null=True, related_name="publications", on_delete=CASCADE)
    pubissue = models.CharField(max_length=24,verbose_name='Vol/Issue', blank=True, null=True)
    platecode = models.CharField(max_length=12, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    backpage = models.TextField(verbose_name='Back page comments (e.g. ads)', blank=True, null=True)
    added = models.DateField(verbose_name='Date added', auto_now=True)
    instrument = models.ForeignKey("Instrument", blank=True, null=True, on_delete=CASCADE)
    #media = models.CharField(max_length=256, blank=True, null=True)
    media = models.FileField(upload_to='', max_length=256, blank=True, null=True)
    source = models.ForeignKey("Source", blank=True, null=True, related_name="+", on_delete=SET_NULL)
    provider = models.ForeignKey('Author', blank=True, null=True, related_name="donations", on_delete=CASCADE)
    digitised = models.BooleanField(default=False)
    material = models.ForeignKey('Material', blank=True, null=True, related_name="+", on_delete=CASCADE)
    condition = models.ForeignKey('Condition', blank=True, null=True, related_name="+", on_delete=CASCADE)
    incomplete = models.BooleanField(default=False)
    # allow nulls initially
    completeness = models.ForeignKey('Completeness', blank=True, null=True, related_name="+", on_delete=SET_NULL)
    duplicate = models.BooleanField(default=False, verbose_name='Already in library?')

    class Meta:
        #unique_together = ('callno', 'category')
        verbose_name_plural = "Entries"
        ordering = ['title','composer__surname']
        permissions = [
            ("march_only", "Can only see marches.")
        ]

    def __str__(self):
        return '%s (%s,%s)' % (self.title, self.category.code, self.callno)

class Publication(models.Model):
    name = models.CharField(max_length=128)
    publisher = models.ForeignKey('Publisher', blank=True, null=True, related_name="publications", on_delete=CASCADE)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('name', 'publisher')
        ordering = ['name',]

    def __str__(self):
        if self.publisher:
            return '%s (%s)' % (self.name, self.publisher.name)
        else:
            return '%s ()' % self.name

class Publisher(models.Model):
    name = models.CharField(max_length=128)
    country = models.ForeignKey('Country', blank=True, null=True, related_name="publishers", on_delete=CASCADE)
    comments = models.TextField(blank=True, null=True)

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
    url = models.URLField(blank=True, null=True)

    def clean(self):
        error_log("SEE_ALSO MODEL CLEAN %s" % str(self))
        if not self.entry and not self.url:  # This will check for None or Empty
            raise ValidationError({'entry': 'At least one of field1 or field2 must have a value.'})
        if self.entry and self.url:  # This will check for None or Empty
            raise ValidationError({'entry': 'Set either entry or URL but not both.'})

    def __str__(self):
        response = ''
        joiner = ''
        if self.entry:
            response += ('%s%s -> E %s' % (joiner, self.source_entry.callno, str(self.entry)))
            joiner = ', '
        if self.url:
            response += '%s%s -> U %s' % (joiner, self.source_entry.callno, str(self.url))

        return response


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
    
    def clean(self):
        if not (self.entry or self.asset):
            raise ValidationError("Specify at least an entry and/or asset")
        
class Folder(models.Model):
    label = models.CharField(max_length=256)
    slot_count = models.IntegerField(default=35)
    issue_date = models.DateField()
    
    def __str__(self):
        return "%s (%d)" % (self.label, self.slot_count)
    
    @property
    def alphabetic(self):
        return self.slots.order_by('entry__label')
    
    @property
    def numeric(self):
        return self.slots.order_by('position')
    
    class Meta:
        verbose_name = "Music Folder"
        ordering = ['label']
    
    
        
    
class FolderItem(models.Model):
    folder = models.ForeignKey(Folder, related_name="slots", on_delete=CASCADE)
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
            return "E %s (%s) " % (str(self.entry), str(self.position))
        else:
            return "C %s (%s) " % (self.comment, str(self.position))
    
