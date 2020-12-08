from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Profile

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(label='Enter username', min_length=4, max_length=100)
    alias = forms.CharField(label='Enter alias', min_length=2, max_length=4)
    gift = forms.CharField(label='Enter desire gift')
    password1 = forms.CharField(label='Enter password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username']
        r = User.objects.filter(username=username)
        if r.count():
            raise ValidationError("Username already exists")
        return username

    def clean_alias(self):
        alias = self.cleaned_data['alias']
        return alias

    def clean_gift(self):
        gift = self.cleaned_data['gift']
        return gift

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Password don't match")

        return password2

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email='',
            password=self.cleaned_data['password1'],
        )
        return user

class SignUpForm(CustomUserCreationForm):
    class Meta:
        model = User
        fields = (
            'username',
            'alias',
            'gift',
            'password1',
            'password2',
        )
