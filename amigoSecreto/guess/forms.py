from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import *
from datetime import timedelta

class SignUpForm(UserCreationForm):
    """ 
    Clase heredada de UserCreationFrom para registrar usuarios.
    Campos: 
        - username: Nombre del usuario.
        - alias: Nombre que aparecera en la interfaz y tendra entre 2 y 4 caracteres.
        - gift: Regalo deseado.
        - password1: Contrasenya.
        - password2: Confirmacion de la contrasenya.
    """
    first_name = forms.CharField(min_length=4, max_length=50)
    last_name = forms.CharField(min_length=4, max_length=50)
    username = forms.CharField(min_length=4, max_length=100)
    alias = forms.CharField(min_length=2, max_length=4)
    gift = forms.CharField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        """ Indicamos el modelo a usar y los campos del form para el registro.
        Dichos campos son: username, alias, gift, password1 y password2."""
        model = User
        fields = (
            'first_name',
            'last_name',
            'username',
            'alias',
            'gift',
            'password1',
            'password2',
        )

    def clean_first_name(self):
        """ Guarda el nombre."""
        first_name = self.cleaned_data['first_name']
        return first_name

    def clean_last_name(self):
        """ Guarda el apellido."""
        last_name = self.cleaned_data['last_name']
        return last_name

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
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        UserData(
            user=user,
            alias=self.cleaned_data['alias'],
            gift=self.cleaned_data['gift'],
        ).save()
        return user

class GameForm(forms.ModelForm):
    """ 
    Clase heredada de forms.Form para crear instancias de juego.
    Campos: 
        - startDate: Fecha de inicio del juego.
        - days: Numero de juegos que durara el juego.
    """
    startDate = forms.DateField()
    days = forms.IntegerField(min_value=6, max_value=12)

    class Meta:
        """ Indicamos el modelo a usar y los campos del form para el registro.
        Dichos campos son: username, alias, gift, password1 y password2."""
        model = Game
        fields = (
            'startDate',
            'days',
        )

    def clean_startDate(self):
        """ Guarda la fecha de inicio del juego."""
        startDate = self.cleaned_data['startDate']
        return startDate

    def clean_days(self):
        """ Guarda el numero de dias que durara el juego."""
        days = self.cleaned_data['days']
        return days

    def gen_round(self, startDate, days):
        select_duration = days*4
        selections = [None]*6
        for i in range(6):
            selections[i] = startDate + timedelta(hours = i*select_duration)
        return selections

    def save(self, commit: bool = True):
        """ Guarda los datos del juego y las rondas en la BD."""
        # Aqui almacenaremos las rondas creadas
        rounds = []
        # Numero de dias que durara el juego
        days = self.cleaned_data['days']
        # Convertimos la fecha de inicio en un datetime.
        startDate = self.cleaned_data['startDate']
        startDate = datetime.datetime(
            year=startDate.year,
            month=startDate.month,
            day=startDate.day
        )

        # Ronda 1
        if days in (9, 12): 
            rounds.append(self.gen_round(startDate, 3))
            startDate += timedelta(days=3)
        else:
            rounds.append(self.gen_round(startDate, 2))
            startDate += timedelta(days=2)

        # Ronda 2
        if days in (8, 9, 11, 12): 
            rounds.append(self.gen_round(startDate, 3))
            startDate += timedelta(days=3)
        else:
            rounds.append(self.gen_round(startDate, 2))
            startDate += timedelta(days=2)

        # Ronda 3
        if days in (7, 8, 9): rounds.append(self.gen_round(startDate, 3))
        elif days > 9: rounds.append(self.gen_round(startDate, 6))
        else: rounds.append(self.gen_round(startDate, 2))

        # Almacenamos los datos del juego.
        game = Game(
            startDate=self.cleaned_data['startDate'],
            days=self.cleaned_data['days'],
            endDate=self.cleaned_data['startDate'] + \
                timedelta(days=self.cleaned_data['days'])
        )
        game.save()

        # Almacenamos los datos de cada ronda.
        for i, r in enumerate(rounds):
            Round(
                game=game,
                firstSelection = r[0],
                secondSelection = r[1],
                thirdSelection = r[2],
                fourthSelection = r[3],
                fifthSelection = r[4],
                sixthSelection = r[5],
            ).save()