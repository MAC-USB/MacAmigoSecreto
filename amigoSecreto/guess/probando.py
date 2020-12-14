from .views import *

print(Group.objects.get(name='Guessing').user_set.all())
