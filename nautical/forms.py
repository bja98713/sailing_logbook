
from django import forms
from .models import LogbookEntry, CrewMember, MediaAsset

class DateTimeLocalInput(forms.DateTimeInput):
    input_type = 'datetime-local'
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('format', '%Y-%m-%dT%H:%M')
        super().__init__(*args, **kwargs)

class LogbookEntryForm(forms.ModelForm):
    crew = forms.ModelMultipleChoiceField(
        queryset=CrewMember.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'size': 8, 'class': 'select-crew'})
    )
    class Meta:
        model = LogbookEntry
        fields = [
            'start_datetime', 'end_datetime', 'departure_port', 'arrival_port',
            'start_position', 'end_position', 'distance_nm', 'avg_speed_kn',
            'weather', 'wind', 'sea_state', 'tide_current', 'avg_course',
            'engine_hours', 'fuel_liters', 'crew', 'notes', 'photos_url', 'cover_photo'
        ]
        widgets = {
            'start_datetime': DateTimeLocalInput(),
            'end_datetime': DateTimeLocalInput(),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

class MediaAssetForm(forms.ModelForm):
    class Meta:
        model = MediaAsset
        fields = ['kind', 'image', 'file', 'caption']

from django import forms
from .models import Consumable

class ConsumableForm(forms.ModelForm):
    class Meta:
        model = Consumable
        fields = ["name", "origin", "reference", "image", "remark", "quantity", "price_eur"]
        widgets = {
            "remark": forms.Textarea(attrs={"rows": 3}),
        }

from .models import Checklist

class ChecklistForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows':3}),
        }


# Form pour les éléments de checklist (permet d'uploader le PDF 'action')
from .models import ChecklistItem

class ChecklistItemForm(forms.ModelForm):
    class Meta:
        model = ChecklistItem
        fields = ['label', 'required', 'action']


# Inline formset (utilisé dans les vues create/update)
from django.forms import inlineformset_factory
ChecklistItemFormSet = inlineformset_factory(
    parent_model=Checklist,
    model=ChecklistItem,
    form=ChecklistItemForm,
    fields=['label', 'required', 'action'],
    extra=1,
    can_delete=True
)


# Chronology form
from .models import Chronology

class ChronologyForm(forms.ModelForm):
    class Meta:
        model = Chronology
        fields = ['date', 'time', 'description', 'action_realisee', 'performer']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'action_realisee': forms.Textarea(attrs={'rows': 2}),
        }
