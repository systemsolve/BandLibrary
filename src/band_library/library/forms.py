from django import forms
from .models import AssetType
from .models import Asset
from .models import AssetStatus
from .utilx import error_log


class MyAssetField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return '%s: %s (%s)' % (obj.manufacturer, obj.model, obj.identifier)


class MyAssetFieldIn(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return '%s: %s (%s) - %s' % (obj.manufacturer, obj.model, obj.identifier, obj.asset_status)


class CheckinForm1(forms.Form):
    # purpose = forms.ModelChoiceField(required=True, choices=[("BAND", "For Band Member"), ("LOAN", "External Borrower"), ("MAINT", "Maintenance")])
    purpose = forms.ModelChoiceField(required=True, queryset=AssetStatus.objects.all())
    instrument = MyAssetFieldIn(widget=forms.RadioSelect, queryset=Asset.objects.filter(asset_status__available=False))         
    
    class Meta:
        exclude = ['asset_type']


class CheckoutForm1(forms.Form):
    # purpose = forms.ModelChoiceField(required=True, choices=[("BAND", "For Band Member"), ("LOAN", "External Borrower"), ("MAINT", "Maintenance")])
    # purpose = forms.ModelChoiceField(required=True, queryset=AssetStatus.objects.filter(available=False))
    instrument_type = forms.ModelChoiceField(empty_label=None, queryset=AssetType.objects.all())
    
    
class CheckoutForm2(forms.Form):
    # instrument_list = MyAssetField(choices=[(instr.pk, instr.identifier) for instr in Asset.objects.all()])
    instrument = MyAssetFieldIn(queryset=Asset.objects.all())
    
    def __init__(self, *args, **kwargs):  
        choice = kwargs.pop('choice', None)
        error_log("CO2: choice %s kwargs %s" % (str(choice), str(kwargs)))
        super().__init__(*args, **kwargs)

        if choice is not None:
            # choicelist = [(instr.pk, instr.identifier) for instr in Asset.objects.filter(asset_type=choice)]
            # self.fields['instrument_list'] = MyAssetField(widget=forms.RadioSelect, choices=choicelist)  
            self.fields['instrument'] = MyAssetFieldIn(widget=forms.RadioSelect, queryset=Asset.objects.filter(asset_type=choice))            
    
    class Meta:
        exclude = ['asset_type']


class CheckoutForm3(forms.Form):
    purpose = forms.ModelChoiceField(required=True, queryset=AssetStatus.objects.all())


class BorrowForm(forms.Form):
    name = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=20)
    email = forms.CharField(max_length=100)
    address = forms.CharField(widget=forms.Textarea)


class MaintForm(forms.Form):
    notes = forms.CharField(widget=forms.Textarea)

