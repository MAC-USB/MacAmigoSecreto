from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
# from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import CreateView, TemplateView
from django.utils.decorators import method_decorator
from .models import *
from .forms import *


class SignInView(LoginView):
    """ Clase heredada de LoginView que representa la vista para el login."""
    template_name = 'templates/signin.html'

class SignUpView(CreateView):
    """ Clase heredada de CreateView que representa la vista para el registro."""
    model = User
    form_class = SignUpForm
    template_name = 'templates/profile_form.html'

    def form_valid(self, form):
        '''
        En este parte, si el formulario es valido guardamos lo que se 
        obtiene de él y usamos authenticate para que el usuario incie 
        sesión luego de haberse registrado y lo redirigimos al index
        '''
        user = form.save()
        login(self.request, user)
        return redirect('/')

class SignOutView(LogoutView):
    """ Clase heredada de LogoutView que representa la vista para el cierre de sesion."""
    pass

class WelcomeView(LoginRequiredMixin, TemplateView):
    """ Clase heredada de TemplateView que representa la vista para la pagina principal.
    En caso de no haber usuario registrado, redirige a la vista del login."""
    template_name = 'templates/welcome.html'

class CreateGameView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """ Clase heredada de CreateView que representa la vista para la creacion de una
    instancia de juego."""
    model = Game
    form_class = GameForm
    template_name = 'templates/game_form.html'

    def test_func(self):
        """ Función para usar con UserPassesTestMixin.
            Permite solo a superusuarios
        """
        return self.request.user.is_superuser

    def form_valid(self, form):
        '''
        En este parte, si el formulario es valido guardamos lo que se 
        obtiene de él.
        '''
        form.save()
        return redirect('/')
