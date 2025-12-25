from django import forms
from django.utils import timezone
from users.models import UserProfile
from .models import Attendance


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["status", "remarks"]
        widgets = {
            "remarks": forms.Textarea(attrs={"rows": 2}),
        }


class AttendanceSheetForm(forms.Form):
    """
    Dynamic form for attendance sheet
    """
    def __init__(self, *args, employees=None, **kwargs):
        super().__init__(*args, **kwargs)

        for emp in employees:
            self.fields[f"status_{emp.id}"] = forms.ChoiceField(
                choices=Attendance.STATUS_CHOICES,
                widget=forms.RadioSelect,
                required=True
            )
            self.fields[f"remarks_{emp.id}"] = forms.CharField(
                required=False,
                widget=forms.TextInput(attrs={"placeholder": "Remarks"})
            )
