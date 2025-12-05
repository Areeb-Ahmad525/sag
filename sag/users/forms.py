from django import forms
from .models import UserProfile

class UserRegistrationForm(forms.Form):
    name = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    father_name = forms.CharField(max_length=150)
    nationality = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=20)
    role = forms.ChoiceField(choices=UserProfile._meta.get_field('role').choices)
    profile_picture = forms.ImageField(required=False)
