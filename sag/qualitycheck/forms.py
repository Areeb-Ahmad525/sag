from django import forms
from .models import QualityInspection


class QualityInspectionForm(forms.ModelForm):
    class Meta:
        model = QualityInspection
        fields = [
            'task_id',
            'inspection_type',
            'result',
            'remarks',
        ]

        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }
