from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Game(models.Model):
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()

class UserData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gift = models.CharField(max_length=50)
    guessed = models.BooleanField(default=False)    #For the final event
    alias = models.CharField(max_length=4, unique=True)

class Teams(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    name = models.CharField(max_length=10)
    score = models.IntegerField()

class GivesTo(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    gifter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gifter')
    gifted = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gifted')

class UserTeam(models.Model):
    team = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Guess(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guess_owner')
    gifter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guess_gifter')
    gifted = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guess_gifted')
    date = models.DateTimeField(User)
    answer = models.BooleanField()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.CharField(max_length=255, blank=True)
    web = models.URLField(blank=True)

    def __str__(self): 
        return self.user.username

@receiver(post_save, sender=User)
def make_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()