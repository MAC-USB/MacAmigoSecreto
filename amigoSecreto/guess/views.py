from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
# from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import CreateView, TemplateView, ListView
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

class GuessView(LoginRequiredMixin, CreateView):
    model = Guess
    template_name = 'templates/guess_form.html'
    form_class = GuessForm

    def get_form_kwargs(self):
        # Esto lo puse para acceder al usuario registrado desde el form.
        kwargs = super(GuessView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        '''
        En este parte, si el formulario es valido guardamos lo que se 
        obtiene de él.
        '''
        form.save()
        return redirect('/')

    def test_func(self):
        # TODO verificar que el usuario esta en Guessing.
        return True

class HistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'templates/history.html'

    def get_context_data(self, **kwargs):
        class Group:
            """ En cada Group guardaremos los owners y los gifters de cada guess
            si pertenecen al mismo selection. """
            def __init__(self, startDate, endDate):
                self.startDate = startDate
                self.endDate = endDate
                self.owners = []
                self.gifters = []

        context = super().get_context_data(**kwargs)

        # Obtenemos el juego actual
        game = Game.objects.latest('startDate')

        # Obtenemos los guess del juego actual
        context['Guess'] = list(Guess.objects.filter(game=game))

        # Obtenemos las fechas de cada seleccion de cada ronda del juego actual
        dates = []
        rounds = list(Round.objects.filter(game=game))
        for round in rounds:
            dates += [
                round.firstSelection, 
                round.secondSelection, 
                round.thirdSelection, 
                round.fourthSelection, 
                round.fifthSelection, 
                round.sixthSelection
            ]

        # Limitamos las fechas hasta la mayor que sea menor a la fecha actual
        for i in range(len(dates)):
            if dates[i] >= make_aware(datetime.now() + timedelta(hours=32)): 
                dates = dates[:i]
                break

        # En esta variable guardaremos cada grupo de guesses
        group_selections = []
        for i in range(len(dates)-1):
            group_selections.append(Group(dates[i], dates[i+1]))

        # Por cada guess.
        for guess in context['Guess']:
            for group in group_selections:
                # Verificamos si la fecha del guess esta en el rango de este grupo.
                if group.startDate <= guess.date < group.endDate:
                    # Si es asi, a;adimos el guess a este grupo
                    group.owners.append(guess.owner)
                    group.gifters.append(guess.gifter)
                    break

        # Eliminamos los grupos vacios.
        i = 0
        while i < len(group_selections):
            if len(group_selections[i].owners) == 0: group_selections.pop(i)
            else: i += 1

        # Reordenamos aleatoriamente cada grupo.
        for group in group_selections:
            shuffle(group.gifters)
            shuffle(group.owners)

        context['Groups'] = group_selections
        return context

class UsersView(LoginRequiredMixin, ListView):
    """ Muestra todos los usuarios registrados junto a su informacion, """
    template_name = 'templates/users.html'
    model = UserData