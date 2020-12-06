from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Game(models.Model):
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()

class UserData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gift = models.CharField(max_length=50)
    guessed = models.BooleanField(default=False)    #For the final event

class Teams(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    name = models.CharField(max_length=10)
    score = models.IntegerField()

class GivesTo(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    gifter = models.ForeignKey(User, on_delete=models.CASCADE)
    gifted = models.ForeignKey(User, on_delete=models.CASCADE)

class UserTeam(models.Model):
    team = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Guess(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    gifter = models.ForeignKey(User, on_delete=models.CASCADE)
    gifted = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(User)
    answer = models.BooleanField()
