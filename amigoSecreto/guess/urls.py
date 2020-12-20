""" guess URL Configuration. """

from django.urls import path
from .views import (
    SignInView, 
    SignUpView, 
    SignOutView, 
    WelcomeView, 
    CreateGameView,
    GuessView, 
    HistoryView, 
    UsersView, 
    RulesView, 
    StartGameView, 
    ForbiddenView
)

urlpatterns = [
    path('', WelcomeView.as_view(), name='home'),
    path('signup/', SignUpView.as_view(), name='sign_up'),
    path('signin/', SignInView.as_view(), name='sign_in'),
    path('signout/', SignOutView.as_view(), name='sign_out'),
    path('create_game/', CreateGameView.as_view(), name='create_game'),
    path('guess/', GuessView.as_view(), name='guess'),
    path('history/', HistoryView.as_view(), name='history'),
    path('users/', UsersView.as_view(), name='users'),
    path('rules/', RulesView.as_view(), name='rules'),
    path('start_game/', StartGameView.as_view(), name='start_game'),
    path('forbidden/', ForbiddenView.as_view(), name='forbidden')
]