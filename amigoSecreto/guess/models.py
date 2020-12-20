""" guess DB Models. """

# Modelos de Django.
from django.db import models
from django.contrib.auth.models import User

# Validadores de Django.
from django.core.validators import MinValueValidator, MaxValueValidator

# Utilidades.
from datetime import date

class Game(models.Model):
    """ 
    Modelo que almacena las instancias de los juegos.
    Campos:
        - startDate: Fecha en la que inicio el juego.
        - days: Numero de dias que durara la fase de adivinanzas. 
            Debe tener un valor entre 6 y 12, incluyendo ambos.
        - endDate: Fecha en la que finaliza la fase de adivinanzas.
        - end: Indica si finalizo el juego.
    """
    startDate = models.DateTimeField()
    days = models.PositiveSmallIntegerField(
        default=6, 
        validators=[MinValueValidator(6), MaxValueValidator(12)]
    )
    endDate = models.DateTimeField(default=date.today)
    gameDay = models.BooleanField(default=False)
    end = models.BooleanField(default=False)

    def __str__(self):
        return f"Game of {self.startDate}"

class UserData(models.Model):
    """ 
    Modelo que almacena los datos del usuario referentes al juego.
    Campos:
        - user: Instancia del modelo User con la informacion basica del usuario.
        - gift: Regalo(s) que desea el usuario.
        - alias: Alias del usuario. Debe tener entre 2 y 4 caracteres, incluyendo ambos.
        - guessed: Indica si ya adivino quien le regala a el.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gift = models.CharField(max_length=50)
    guessed = models.BooleanField(default=False)  
    alias = models.CharField(max_length=4, unique=True)

    def __str__(self):
        return self.alias

class Teams(models.Model):
    """ 
    Modelo que almacena los datos de los equipos.
    Campos:
        - game: Instancia del modelo Game al que pertenece el equipo.
        - name: Nombre del equipo.
        - score: Puntaje actual del equipo.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    name = models.CharField(max_length=10)
    score = models.PositiveSmallIntegerField(default=0, blank=True)

    def __str__(self):
        return self.name

class GivesTo(models.Model):
    """ 
    Modelo que almacena las relaciones "X le regala a Y".
    Campos:
        - game: Instancia del modelo Game al que pertenece la relacion.
        - gifter: Instancia del modelo User que entrega el regalo.
        - gifted: Instancia del modelo User que recibe el regalo.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    gifter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gifter')
    gifted = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gifted')

    def __str__(self):
        return f"{self.gifter} give to {self.gifted}"

class UserTeam(models.Model):
    """ 
    Modelo que almacena las relaciones "X pertenece al equipo Y".
    Campos:
        - user: Instancia del modelo User.
        - team: Instancia del modelo Teams al que pertenece el usuario.
    """
    team = models.ForeignKey(Teams, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} belongs to team {self.team}"

class Guess(models.Model):
    """ 
    Modelo que almacena las adivinanzas.
    Campos:
        - game: Instancia del modelo Game al que pertenece la adivinanza.
        - owner: Instancia del modelo User que realiza la adivinanza.
        - gifter: Instancia del modelo User que entrega el regalo.
        - gifted: Instancia del modelo User que recibe el regalo.
        - date: Fecha en la que se realizo la adivinanza.
        - answer: Respuesta que le dio la app al owner.

    En resumen, una instancia de Guess representa que:
    OWNER pregunto si GIFTER le regala a GIFTED y obtuvo como respuesta: ANSWER.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guess_owner')
    gifter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guess_gifter')
    gifted = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guess_gifted')
    date = models.DateTimeField()
    answer = models.BooleanField()

    def __str__(self):
        return f"{self.owner} asked if {self.gifter} gives to {self.gifted}. Answer: {self.answer}."

class Round(models.Model):
    """ 
    Modelo que almacena las rondas de un juego.
    Campos:
        - game: Instancia del modelo Game al que pertenece la ronda.
        - firstSelection: Fecha en la que se realizara la primera seleccion.
        - secondSelection: Fecha en la que se realizara la segunda seleccion.
        - thirdSelection: Fecha en la que se realizara la tercera seleccion.
        - fourthSelection: Fecha en la que se realizara la cuarta seleccion.
        - fifthSelection: Fecha en la que se realizara la quinta seleccion.
        - sixthSelection: Fecha en la que se realizara la sexta seleccion.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    firstSelection = models.DateTimeField()
    secondSelection = models.DateTimeField()
    thirdSelection = models.DateTimeField()
    fourthSelection = models.DateTimeField()
    fifthSelection = models.DateTimeField()
    sixthSelection = models.DateTimeField()

class Options(models.Model):
    """ 
    Modelo que almacena las opciones que tiene un usuario al realizar una
    adivinanza.
    Campos:
        - round: Instancia del modelo Round al que pertenece esta instancia.
        - user: Instancia del modelo User.
        - option1: Instancia del modelo User que representa una de las opciones.
        - option2: Instancia del modelo User que representa una de las opciones.
        - option3: Instancia del modelo User que representa una de las opciones.
    """
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    option1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='option1')
    option2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='option2')
    option3 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='option3')

    def __str__(self):
        return f"{self.user} have options {self.option1}, {self.option2} and {self.option3}"

class Junior(models.Model):
    """ Shuuuuuuuuniorrrrrrrrrrr."""
    name = models.CharField(max_length=50)
    sound = models.FileField()
    photo = models.FileField()