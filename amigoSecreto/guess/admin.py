from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(UserData)
admin.site.register(Game)
admin.site.register(Round)
admin.site.register(Teams)
admin.site.register(GivesTo)
admin.site.register(UserTeam)
admin.site.register(Guess)
admin.site.register(Options)