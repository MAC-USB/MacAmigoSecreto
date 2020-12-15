from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta, date, datetime

class Game(models.Model):
    startDate = models.DateTimeField()
    days = models.PositiveSmallIntegerField(
        default=6, validators=[MinValueValidator(6), MaxValueValidator(12)])
    endDate = models.DateTimeField(default=date.today)

    def __str__(self):
        return f"Game of {self.startDate}"

class UserData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gift = models.CharField(max_length=50)
    guessed = models.BooleanField(default=False)    #For the final event
    alias = models.CharField(max_length=4, unique=True)

    def __str__(self):
        return self.alias

class Teams(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    name = models.CharField(max_length=10)
    score = models.PositiveSmallIntegerField(default=0, blank=True)

    def __str__(self):
        return self.name

class GivesTo(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    gifter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gifter')
    gifted = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gifted')

    def __str__(self):
        return f"{self.gifter} give to {self.gifted}"

class UserTeam(models.Model):
    team = models.ForeignKey(Teams, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} belongs to team {self.team}"

class Guess(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guess_owner')
    gifter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guess_gifter')
    gifted = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guess_gifted')
    date = models.DateTimeField(User)
    answer = models.BooleanField()

class Round(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    firstSelection = models.DateTimeField()
    secondSelection = models.DateTimeField()
    thirdSelection = models.DateTimeField()
    fourthSelection = models.DateTimeField()
    fifthSelection = models.DateTimeField()
    sixthSelection = models.DateTimeField()

class Options(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    option1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='option1')
    option2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='option2')
    option3 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='option3')

    def __str__(self):
        return f"{self.user} have options {self.option1}, {self.option2} and {self.option3}"