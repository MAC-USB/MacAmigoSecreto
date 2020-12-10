from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserData

class CustomUserCreationForm(UserCreationForm):
    """ 
    Clase heredada de UserCreationFrom.
    Campos: 
        - username: Nombre del usuario.
        - alias: Nombre que aparecera en la interfaz y tendra entre 2 y 4 caracteres.
        - gift: Regalo deseado.
        - password1: Contrasenya.
        - password2: Confirmacion de la contrasenya.
    """
    username = forms.CharField(label='Enter username', min_length=4, max_length=100)
    alias = forms.CharField(label='Enter alias', min_length=2, max_length=4)
    gift = forms.CharField(label='Enter desire gift')
    password1 = forms.CharField(label='Enter password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    def clean_username(self):
        """ Guarda el username y verifica que se encuentre en uso."""
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists")
        return username

    def clean_alias(self):
        """ Guarda el alias."""
        alias = self.cleaned_data['alias']
        if UserData.objects.filter(alias=alias).exists():
            raise ValidationError("Alias already exists")
        return alias

    def clean_gift(self):
        """ Guarda el regalo deseado."""
        gift = self.cleaned_data['gift']
        return gift

    def clean_password2(self):
        """ Verifica que ambas contrasenyas coinciden y la guarda."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError("Password don't match")
        return password2

    def save(self, commit: bool = True):
        """ Guarda los datos del usuario en la BD."""
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email='',
            password=self.cleaned_data['password1'],
        )
        UserData(
            user=user,
            alias=self.cleaned_data['alias'],
            gift=self.cleaned_data['gift'],
        ).save()
        return user

class SignUpForm(CustomUserCreationForm):
    """ Clase heredada de CustomUserCreationFrom."""
    class Meta:
        """ Indicamos el modelo a usar y los campos del form para el registro.
        Dichos campos son: username, alias, gift, password1 y password2."""
        model = User
        fields = (
            'username',
            'alias',
            'gift',
            'password1',
            'password2',
        )
