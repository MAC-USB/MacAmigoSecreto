from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib import messages
# from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import CreateView, TemplateView, ListView, FormView
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Verificamos si hay algun juego activo
        context['game_active'] = bool(len(Game.objects.all()))

        class TeamsData:
            """ Clase donde almacenamos los datos de los teams. """
            def __init__(self, name, score):
                self.name = name
                self.score = score
                self.users = []

        # Obtenemos el juego actual
        game = Game.objects.latest('startDate')

        # Obtenemos los equipos del juego actual
        teams = list(Teams.objects.filter(game=game))
        teams = [TeamsData(team.name, team.score) for team in teams]

        # Agrupamos los usuarios
        for user_team in UserTeam.objects.all():
            for team in teams:
                if user_team.team.name == team.name:
                    team.users.append(UserData.objects.filter(user=user_team.user)[0])

        context['Teams'] = teams

        # Fecha actual.
        context['date'] = make_aware(datetime.now()).strftime('%b %d, %Y %H:%M:%S')
        # Fecha final del juego.
        context['end_date'] = game.endDate.strftime('%b %d, %Y %H:%M:%S')
        # Verificamos si ya pasamos la fecha final.
        context['end_countdown'] = make_aware(datetime.now()) >= game.endDate

        # La persona que esta adivinando
        try: context['guessing'] = list(Group.objects.get(name='Guessing').user_set.all())[0]
        except: context['guessing'] = ""

        # Inicio el juego
        context['start_game'] = not game.gameDay

        return context

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

    def handle_no_permission(self):
        messages.add_message(self.request, messages.INFO, "You must be a superuser.")
        return redirect('/forbidden/')

class GuessView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
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
        # Verifcamos que el usuario esta en Guessing.
        return self.request.user.groups.filter(name = "Guessing").exists()

    def handle_no_permission(self):
        messages.add_message(self.request, messages.INFO, "It's not your turn to guess yet.")
        return redirect('/forbidden/')

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
            if dates[i] >= make_aware(datetime.now()): 
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

class RulesView(LoginRequiredMixin, TemplateView):
    '''Clase heredada de TemplateView que representa la vista de las reglas del juego'''
    template_name = 'templates/rules.html'

class StartGameView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    form_class = StartGameForm
    template_name = 'templates/init_game_form.html'

    def test_func(self):
        """ Función para usar con UserPassesTestMixin.
            Permite solo a superusuarios
        """
        # Condiciones para ver esta vista:
        # Ser super usuarios
        self.cond1 = self.request.user.is_superuser
        # Que ya se haya alcanzado la fecha limite del ultimo juego creado
        self.cond2 = make_aware(datetime.now() + timedelta(days=30)) >= Game.objects.latest('startDate').endDate
        # Que el ultimo juego creado no haya sido iniciado
        self.cond3 = not Game.objects.latest('startDate').gameDay
        return self.cond1 and self.cond2 and self.cond3

    def form_valid(self, form):
        '''
        En este parte, si el formulario es valido guardamos lo que se 
        obtiene de él.
        '''
        form.save()
        return redirect('/')

    def handle_no_permission(self):
        if not self.cond1:
            messages.add_message(
                self.request, 
                messages.INFO, 
                "You must be a superuser."
            )
        elif not self.cond2:
            messages.add_message(
                self.request, 
                messages.INFO, 
                "The last game has not finished the guessing phase yet."
            )
        else:
            messages.add_message(
                self.request, 
                messages.INFO, 
                "The last game is already in the game day phase."
            )
        return redirect('/forbidden/')

class ForbiddenView(LoginRequiredMixin, TemplateView):
    template_name = 'templates/forbidden.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        storage = messages.get_messages(self.request)
        context['forbidden_message'] = list(storage)[-1]
        storage.used = False
        return context
