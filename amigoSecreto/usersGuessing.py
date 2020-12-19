from guess.forms import *

print(Group.objects.get(name='Guessing').user_set.all())