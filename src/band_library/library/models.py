from __future__ import unicode_literals

from django.db import models

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


class Entry(models.Model):
    title = models.CharField(max_length=200)
    callno = LabelField(max_length=12, verbose_name="label", db_column="label")
    duration = models.CharField(max_length=8, default="0:0")
    composer = models.ForeignKey('Author', blank=True, null=True, related_name="compositions")
    arranger = models.ForeignKey('Author', blank=True, null=True, related_name="arrangements")
    category = models.ForeignKey('Category')
    comments = models.TextField(blank=True, null=True)
    added = models.DateField(verbose_name='Date added', auto_now=True)
    instrument = models.ForeignKey("Instrument", blank=True, null=True)
    #media = models.CharField(max_length=256, blank=True, null=True)
    media = models.FileField(upload_to='', max_length=256, blank=True, null=True)

    class Meta:
        #unique_together = ('callno', 'category')
        verbose_name_plural = "Entries"
        ordering = ['title','composer__surname']
        permissions = [
            ("march_only", "Can only see marches.")
        ]

    def __unicode__(self):
        return u'%s (%s,%s)' % (self.title, self.category.code, self.callno)

class Author(models.Model):
    surname = models.CharField(max_length=32)
    given = models.CharField(max_length=48, blank=True, null=True)
    bornyear = models.IntegerField(blank=True, null=True, verbose_name='Year of Birth')
    diedyear = models.IntegerField(blank=True, null=True, verbose_name='Year of Death')
    country = models.ForeignKey('Country', blank=True, null=True, related_name="authors")
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('surname', 'given')
        ordering = ['surname', 'given']

    def __unicode__(self):
        if self.given:
            return u'%s, %s' % (self.surname, self.given)
        else:
            return u'%s' % self.surname

class Country(models.Model):
    name = models.CharField(max_length=48)
    isocode = models.CharField(max_length=3)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.code)

class Instrument(models.Model):
    name = models.CharField(max_length=48)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)

class Category(models.Model):
    label = models.CharField(max_length=32)
    code = models.CharField(max_length=2)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['label']

    def __unicode__(self):
        return u'%s (%s)' % (self.label, self.code)

class Program(models.Model):
    included = models.DateField()
    comments = models.TextField(blank=True, null=True)
    entry = models.ForeignKey('Entry', related_name="programmed")

    def __unicode__(self):
        return u'%s' % (self.included)





