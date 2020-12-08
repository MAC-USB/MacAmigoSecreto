from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView 
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, TemplateView
from django.utils.decorators import method_decorator
from .models import Profile
from .forms import SignUpForm

class SignInView(LoginView):
    template_name = 'guess/signin.html'

class SignUpView(CreateView):
    model = Profile
    form_class = SignUpForm

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
    pass

@method_decorator(login_required, name='dispatch')
class WelcomeView(TemplateView):
   template_name = 'guess/welcome.html'

