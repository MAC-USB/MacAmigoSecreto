from guess.forms import *

for user in Group.objects.get(name='Guessing').user_set.all():
    print(user, "<=", GivesTo.objects.filter(gifted=user)[0].gifter)
