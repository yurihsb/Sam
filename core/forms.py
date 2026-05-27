from django import forms
from django.contrib.auth.models import User
from core.models import UserProfile

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'birth_date']
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'birth_date']

