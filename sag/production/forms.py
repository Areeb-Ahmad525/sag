from django import forms
from django.contrib.auth.models import User

from production.models import ProductionTask
from users.models import Team
from users import constants


class ProductionTaskForm(forms.ModelForm):
    class Meta:
        model = ProductionTask
        fields = ['name', 'assigned_to', 'remarks']
        labels = {
            'name': 'Task Name',
            'assigned_to': 'Assign To',
            'remarks': 'Remarks',
        }

    def __init__(self, *args, **kwargs):
        manager_profile = kwargs.pop('manager_profile', None)
        super().__init__(*args, **kwargs)

        # -------------------------------
        # Default: empty dropdown
        # -------------------------------
        self.fields['assigned_to'].queryset = User.objects.none()
        self.fields['assigned_to'].empty_label = "Select employee"

        # -------------------------------
        # Team-based employee filtering
        # -------------------------------
        if manager_profile:
            team = Team.objects.filter(manager=manager_profile).first()

            if team:
                employee_profiles = team.members.filter(
                    role=constants.ROLE_EMPLOYEE,
                    status='active'
                )

                self.fields['assigned_to'].queryset = (
                    User.objects
                    .filter(
                        userprofile__in=employee_profiles,
                        is_active=True
                    )
                    .select_related('userprofile')
                )

        # -------------------------------
        # 🔥 SHOW USERPROFILE NAME (FIX)
        # -------------------------------
        self.fields['assigned_to'].label_from_instance = (
            lambda user: user.userprofile.name
        )

        # -------------------------------
        # UI polish (Bootstrap)
        # -------------------------------
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'e.g. Cutting'
        })

        self.fields['assigned_to'].widget.attrs.update({
            'class': 'form-select'
        })

        self.fields['remarks'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3
        })
