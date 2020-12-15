"""guess URL Configuration"""

from django.urls import path
from .views import *

urlpatterns = [
    path('', WelcomeView.as_view(), name='home'),
    path('signup/', SignUpView.as_view(), name='sign_up'),
    path('signin/', SignInView.as_view(), name='sign_in'),
    path('signout/', SignOutView.as_view(), name='sign_out'),
    path('create_game/', CreateGameView.as_view(), name='create_game'),
    path('guess/', GuessView.as_view(), name='guess'),
]