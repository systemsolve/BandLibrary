

from django.db import models
from django.db.models.deletion import CASCADE, SET_NULL

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


class Entry(models.Model):
    title = models.CharField(max_length=200)
    callno = LabelField(max_length=12, verbose_name="label", db_column="label")
    pagecount = models.IntegerField(blank=True, null=True, verbose_name="Page count", help_text="for solo cornet")
    duration = models.CharField(max_length=8, default="0:0")
    composer = models.ForeignKey('Author', blank=True, null=True, related_name="compositions", on_delete=CASCADE)
    arranger = models.ForeignKey('Author', blank=True, null=True, related_name="arrangements", on_delete=CASCADE)
    category = models.ForeignKey('Category', verbose_name='Shelving Category', on_delete=CASCADE)
    genre = models.ForeignKey('Genre', verbose_name='Type/Genre of Work', blank=True, null=True, on_delete=SET_NULL)
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
    condition = models.ForeignKey('Condition', blank=True, null=True, related_name="+", on_delete=CASCADE)
    incomplete = models.BooleanField(default=False)

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
    included = models.DateField()
    comments = models.TextField(blank=True, null=True)
    entry = models.ManyToManyField('Entry', related_name="programmed")

    def __str__(self):
        return '%s' % (self.included)





