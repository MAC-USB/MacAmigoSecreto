from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Game(models.Model):
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()

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
    score = models.IntegerField()

    def __str__(self):
        return self.name

class GivesTo(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    gifter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gifter')
    gifted = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gifted')

class UserTeam(models.Model):
    team = models.ForeignKey(Game, on_delete=models.CASCADE)
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

    def __str__(self):
        return f"{self.owner}'s guess of {self.date}'"

class Profile(models.Model):
    """ Modelo base de usuario. """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.CharField(max_length=255, blank=True)
    web = models.URLField(blank=True)

    def __str__(self): 
        return self.user.username

@receiver(post_save, sender=User)
def make_user_profile(sender, instance, created, **kwargs):
    """ Crea el perfil del usuairo."""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """ Guarda el perfil del usuario."""
    instance.profile.save()