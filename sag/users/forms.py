# users/forms.py
from django import forms
from .models import UserProfile
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
