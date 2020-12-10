from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.models import User 
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, TemplateView
from django.utils.decorators import method_decorator
from .models import UserData
from .forms import SignUpForm

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

@method_decorator(login_required, name='dispatch')
class WelcomeView(TemplateView):
    """ Clase heredada de TemplateView que representa la vista para la pagina principal.
    En caso de no haber usuario registrado, redirige a la vista del login."""
    template_name = 'templates/welcome.html'

