from django import forms
from .models import CareSchedule

class CareScheduleForm(forms.ModelForm):
    class Meta:
        model = CareSchedule
        fields = ['plant', 'task', 'date', 'interval_days']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
