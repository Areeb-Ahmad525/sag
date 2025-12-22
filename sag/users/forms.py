# users/forms.py
from django import forms
from .models import UserProfile,Team
from django.contrib.auth.models import User

class UserRegistrationForm(forms.Form):
    name = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    father_name = forms.CharField(max_length=150, required=False)
    nationality = forms.CharField(max_length=100, required=False)
    phone = forms.CharField(max_length=20, required=False)
    role = forms.ChoiceField(choices=UserProfile._meta.get_field('role').choices)
    profile_picture = forms.ImageField(required=False)

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        # allow users to update only safe fields (role change is NOT allowed here)
        fields = ['name', 'father_name', 'nationality', 'phone', 'profile_picture']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }






from django import forms
from .models import Team, UserProfile
from . import constants

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'manager', 'members']
        widgets = {
            'manager': forms.Select(attrs={'class': 'manager-select'}), # Added class
            'members': forms.SelectMultiple(attrs={'id': 'id_members_hidden', 'style': 'display:none;'}),
        }

    def __init__(self, *args, **kwargs):
        super(TeamForm, self).__init__(*args, **kwargs)
        
        # This still provides the searchable text for the dropdown
        self.fields['manager'].label_from_instance = self.get_manager_label

        already_managed = Team.objects.values_list('manager_id', flat=True)
        already_members = Team.objects.values_list('members', flat=True)
        assigned_ids = set(list(already_managed) + [m for m in already_members if m is not None])

        manager_qs = UserProfile.objects.filter(
            role=constants.ROLE_MANAGER, 
            status='active'
        ).exclude(id__in=assigned_ids)

        member_qs = UserProfile.objects.filter(
            role=constants.ROLE_EMPLOYEE,
            status='active'
        ).exclude(id__in=assigned_ids)

        if self.instance.pk:
            manager_qs = (manager_qs | UserProfile.objects.filter(id=self.instance.manager_id)).distinct()
            member_qs = (member_qs | self.instance.members.all()).distinct()

        self.fields['manager'].queryset = manager_qs
        self.fields['members'].queryset = member_qs


    def get_manager_label(self, obj):
        # We also include the image URL in the label data for JS to grab
        img_url = obj.profile_picture.url if obj.profile_picture else ""
        return f"{obj.name}|S/O: {obj.father_name or 'N/A'}|{obj.user.email}|{img_url}"