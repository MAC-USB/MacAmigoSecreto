""" guess Views. """

# Modelos de Django.
from django.contrib.auth.models import User, Group

# Utilidades de Django.
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import login
from django.utils.timezone import make_aware
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Vistas de Django.
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, TemplateView, ListView, FormView

# Nuestros Forms.
from .forms import SignUpForm, GameForm, GuessForm, StartGameForm

# Nuestros Modelos.
from .models import Game, UserData, Teams, UserTeam, Guess, Round

# Utilidades
from datetime import timedelta, datetime
from random import shuffle


class SignInView(LoginView):
    """ Clase heredada de LoginView que representa la vista para el login."""
    template_name = 'templates/signin.html'

class SignUpView(CreateView):
    """ Clase heredada de CreateView que representa la vista para el registro."""
    model = User
    form_class = SignUpForm
    template_name = 'templates/profile_form.html'

    def form_valid(self, form):
        """
        En este parte, si el formulario es valido guardamos lo que se 
        obtiene de él, usamos login para que el usuario inicie 
        sesión luego de haberse registrado y lo redirigimos al Welcome.
        """
        user = form.save()
        login(self.request, user)
        return redirect('/')

class SignOutView(LogoutView):
    """ Clase heredada de LogoutView que representa la vista para el cierre de sesion."""
    pass

class WelcomeView(LoginRequiredMixin, TemplateView):
    """ 
    Clase que representa la vista para la pagina principal. 
    Hereda de las clases:
        - LoginRequiredMixin: Se requiere que haya un usuario en sesion.
        - TemplateView: View general de Django.
    """
    template_name = 'templates/welcome.html'

    def get_context_data(self, **kwargs):
        """ 
        Se definen las siguientes variables de contexto:
            - game_active: Indica si hay algun juego activo.
            - teams: Contiene la informacion de los equipos en el juego.
            - date: Fecha actual.
            - end_date: Fecha en la que termina la fase de adivinanzas.
            - end_countdown: Booleano que indica si ya pasamos el end_date.
            - guessing: Usuario que esta actualmente adivinando.
            - start_game: Indica si ya inicio la fase del dia del juego.
            - end_game: Indica si ya se termino el juego.
            - winners: Equipo ganador.
        """
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

        # Finalizo el juego
        context['end_game'] = game.end
        if context['end_game']:
            # Si ya finalizo el juego, indicamos el equipo ganador.
            if teams[0].score < teams[1].score: context['winners'] = teams[0].name
            else: context['winners'] = teams[1].name

        return context

class CreateGameView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """ 
    Clase que representa la vista para la creacion de una instancia de juego. 
    Hereda de las clases:
        - LoginRequiredMixin: Se requiere que haya un usuario en sesion.
        - UserPassesTestMixin: Para requerir que el usuario sea superusuario.
        - CreateView: View de Django para crear instancia de algun Modelo.
    """
    model = Game
    form_class = GameForm
    template_name = 'templates/game_form.html'

    def test_func(self):
        """ Permitimos solo a superusuarios."""
        return self.request.user.is_superuser

    def form_valid(self, form):
        """ En este parte, si el formulario es valido guardamos lo que 
        se obtiene de él."""
        form.save()
        return redirect('/')

    def handle_no_permission(self):
        """ Si algun usuario no superusuario intenta acceder a la pagina, se le redirigira
        a la pagina Forbidden. """
        messages.add_message(self.request, messages.INFO, "You must be a superuser.")
        return redirect('/forbidden/')

class GuessView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """ 
    Clase que representa la vista para adivinar. 
    Hereda de las clases:
        - LoginRequiredMixin: Se requiere que haya un usuario en sesion.
        - UserPassesTestMixin: Para requerir que el usuario sea superusuario.
        - CreateView: View de Django para crear instancia de algun Modelo.
    """
    model = Guess
    template_name = 'templates/guess_form.html'
    form_class = GuessForm

    def get_form_kwargs(self):
        """ Permitimos al Form acceder a los datos del usuario pasando su instancia
        como un argumento."""
        kwargs = super(GuessView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        """ En este parte, si el formulario es valido guardamos lo que se 
        obtiene de él. """
        form.save()
        return redirect('/')

    def test_func(self):
        """ Permitimos a usuarios que se encuentren en el grupo Guessing. """
        return self.request.user.groups.filter(name = "Guessing").exists()

    def handle_no_permission(self):
        """ Si el usuario no se encuentra en el grupo Guessing, se le redirigira
        a la pagina Forbidden. """
        messages.add_message(self.request, messages.INFO, "It's not your turn to guess yet.")
        return redirect('/forbidden/')

class HistoryView(LoginRequiredMixin, TemplateView):
    """ 
    Clase que representa la vista para los historiales publico y privado. 
    Hereda de las clases:
        - LoginRequiredMixin: Se requiere que haya un usuario en sesion.
        - TemplateView: View general de Django.
    """
    template_name = 'templates/history.html'

    def get_context_data(self, **kwargs):
        """ 
        Se definen las siguientes variables de contexto:
            - guess: Lista de instancias de adivinanzas en el juego.
            - groups: Contiene la informacion de los gifters y gifteds de los
                guess por cada seleccion.
        """
        context = super().get_context_data(**kwargs)
        class Group:
            """ En cada Group guardaremos los owners y los gifters de cada guess
            si pertenecen al mismo selection. """
            def __init__(self, startDate, endDate):
                self.startDate = startDate
                self.endDate = endDate
                self.owners = []
                self.gifters = []

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
    """ 
    Clase que representa la vista de los usuarios registrados. 
    Hereda de las clases:
        - LoginRequiredMixin: Se requiere que haya un usuario en sesion.
        - ListView: View de Django para mostrar una lista de instancias de
            algun modelo.
    """
    template_name = 'templates/users.html'
    model = UserData

class RulesView(LoginRequiredMixin, TemplateView):
    """ 
    Clase que representa la vista para las reglas. 
    Hereda de las clases:
        - LoginRequiredMixin: Se requiere que haya un usuario en sesion.
        - TemplateView: View general de Django.
    """
    template_name = 'templates/rules.html'

class StartGameView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """ 
    Clase que representa la vista para iniciar la fase de dia del juego. 
    Hereda de las clases:
        - LoginRequiredMixin: Se requiere que haya un usuario en sesion.
        - UserPassesTestMixin: Para requerir que:
            * El usuario sea superusuario.
            * El ultimo juego creado pasado haya pasado la fase de adivinanzas.
            * El ultimo juego creado no se encuentre ya en la fase de dia del juego.
        - CreateView: View de Django para crear instancia de algun Modelo.
    """
    form_class = StartGameForm
    template_name = 'templates/init_game_form.html'

    def test_func(self):
        """ 
        Para entrar a la vista se requiere que:
            * El usuario sea superusuario.
            * El ultimo juego creado pasado haya pasado la fase de adivinanzas.
            * El ultimo juego creado no se encuentre ya en la fase de dia del juego.
        """
        # Guardamos las condiciones como atributos de la isntancia actual porque luego
        # las necesitaremos.

        # Ser super usuarios
        self.cond1 = self.request.user.is_superuser
        # Que ya se haya alcanzado la fecha limite del ultimo juego creado
        self.cond2 = make_aware(datetime.now()) >= Game.objects.latest('startDate').endDate
        # Que el ultimo juego creado no haya sido iniciado
        self.cond3 = not Game.objects.latest('startDate').gameDay
        return self.cond1 and self.cond2 and self.cond3

    def form_valid(self, form):
        """ En este parte, si el formulario es valido guardamos lo que se 
        obtiene de él. """
        form.save()
        return redirect('/')

    def handle_no_permission(self):
        """ Si el usuario no cumple las condiciones, se le redirigira
        a la pagina Forbidden. """

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
    """ 
    Clase que representa la vista Forbidden, al cual se accede cuando algun
    usuario intenta acceder a alguna vista sin los permisos necesarios. 
    Hereda de las clases:
        - LoginRequiredMixin: Se requiere que haya un usuario en sesion.
        - TemplateView: View general de Django.
    """
    template_name = 'templates/forbidden.html'

    def get_context_data(self, **kwargs):
        """ 
        Se definen las siguientes variables de contexto:
            - forbidden_message: Mensaje con la razon por la cual el usuario
                entro a la pagina forbidden.
        """
        context = super().get_context_data(**kwargs)
        storage = messages.get_messages(self.request)
        context['forbidden_message'] = list(storage)[-1]
        # Indicamos que todavia necesitamos los mensajes, por lo que no 
        # deben borrarse.
        storage.used = False
        return context
