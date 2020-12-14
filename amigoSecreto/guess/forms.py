from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware
from .models import *
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from random import shuffle

class SignUpForm(UserCreationForm):
    """ 
    Clase heredada de UserCreationFrom para registrar usuarios.
    Campos: 
        - username: Nombre del usuario.
        - alias: Nombre que aparecera en la interfaz y tendra entre 2 y 4 caracteres.
        - gift: Regalo deseado.
        - password1: Contrasenya.
        - password2: Confirmacion de la contrasenya.
    """
    first_name = forms.CharField(min_length=4, max_length=50)
    last_name = forms.CharField(min_length=4, max_length=50)
    username = forms.CharField(min_length=4, max_length=100)
    alias = forms.CharField(min_length=2, max_length=4)
    gift = forms.CharField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        """ Indicamos el modelo a usar y los campos del form para el registro.
        Dichos campos son: username, alias, gift, password1 y password2."""
        model = User
        fields = (
            'first_name',
            'last_name',
            'username',
            'alias',
            'gift',
            'password1',
            'password2',
        )

    def clean_first_name(self):
        """ Guarda el nombre."""
        first_name = self.cleaned_data['first_name']
        return first_name

    def clean_last_name(self):
        """ Guarda el apellido."""
        last_name = self.cleaned_data['last_name']
        return last_name

    def clean_username(self):
        """ Guarda el username y verifica que se encuentre en uso."""
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists")
        return username

    def clean_alias(self):
        """ Guarda el alias."""
        alias = self.cleaned_data['alias']
        if UserData.objects.filter(alias=alias).exists():
            raise ValidationError("Alias already exists")
        return alias

    def clean_gift(self):
        """ Guarda el regalo deseado."""
        gift = self.cleaned_data['gift']
        return gift

    def clean_password2(self):
        """ Verifica que ambas contrasenyas coinciden y la guarda."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError("Password don't match")
        return password2

    def save(self, commit: bool = True):
        """ Guarda los datos del usuario en la BD."""
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email='',
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        UserData(
            user=user,
            alias=self.cleaned_data['alias'],
            gift=self.cleaned_data['gift'],
        ).save()
        return user

class GameForm(forms.ModelForm):
    """ 
    Clase heredada de forms.Form para crear instancias de juego.
    Campos: 
        - startDate: Fecha de inicio del juego.
        - days: Numero de juegos que durara el juego.
    """
    startDate = forms.DateField(initial=date.today() + timedelta(days=1))
    days = forms.IntegerField(min_value=6, max_value=12)

    class Meta:
        """ Indicamos el modelo a usar y los campos del form para el registro.
        Dichos campos son: username, alias, gift, password1 y password2."""
        model = Game
        fields = (
            'startDate',
            'days',
        )

    def clean_startDate(self):
        """ Guarda la fecha de inicio del juego."""
        startDate = self.cleaned_data['startDate']
        if startDate <= date.today():
            raise forms.ValidationError('The date must be at least tomorrow.')
        return startDate

    def clean_days(self):
        """ Guarda el numero de dias que durara el juego."""
        days = self.cleaned_data['days']
        return days

    def gen_round(self, startDate, days):
        """ Genera las fechas de las selecciones de una ronda segun su fecha de inicio
        y el tiempo que durara."""
        # Las selecciones duran en horas 4 veces el numero de dias que dura la ronda.
        # Ronda de 2, 3, 6 dias -> selecciones de 8, 12, 24 horas respectivamente.
        select_duration = days*4
        selections = [None]*6
        for i in range(6):
            # Usamos make_aware para agregar la zona horaria
            selections[i] = make_aware(startDate + timedelta(hours = i*select_duration))
        return selections

    def create_teams(self):
        """ Separa todos los usuarios en User en dos equipos: Lobos y aldeanos, 
        creando las instancias de Team y UserTeam correspondientes."""
        # Almacenamos la instancia de todos los jugadores
        # TODO hay que definir aquí si van a ser todos los usuarios o si el superusuario los 
        # va agregando
        users = list(User.objects.all())

        # Creamos unos indices con el numero de participantes y los ordenamos aleatoriamente.
        N = len(users)
        indexes = [i for i in range(N)]
        shuffle(indexes)

        # Separamos en lobos y aldeanos.
        wolfs = [users[i] for i in indexes[:N//2]]
        villagers = [users[i] for i in indexes[N//2:]]

        # El último juego creado es el activo
        game = Game.objects.latest('startDate')

        # Creamos el equipo lobo para el juego actual
        wolfs_team = Teams.objects.get_or_create(game=game, name='Wolfs')[0]#, score=0)
        for wolf in wolfs:
            UserTeam.objects.create(team=wolfs_team, user=wolf)

        # Creamos el equipo aldeano para el juego actual
        villagers_team = Teams.objects.get_or_create(game=game, name='Villagers')[0]#, score=0)
        for villager in villagers:
            UserTeam.objects.create(team=villagers_team, user=villager)

    def get_set_options(self, group, round, options, first_selection):
        """ 
        Genera una funcion que actualiza la BD dada la seleccion actual. Dicha
        funcion sera la que ejecutara un job en la fecha indicada.
        INPUTS:
            - group: Lista de instancias UserTeam, los cuales son los usuarios que
                        van a intentar adivinar en esta ronda.
            - round: Instancia de Round que representa la ronda actual.
            - options: Conjunto de opciones que tiene cada usuario de group para hacer
                        la adivinanza. options[i] corresponde a las opciones de group[i].
            - first_selection: Indica si es la primera seleccion de la ronda.
        """
        def set_options(
            group=group,
            round=round, 
            options=options, 
            first_selection=first_selection
        ):
            # Obtenemos los 3 grupos
            guessing = Group.objects.get(name='Guessing')
            guessed = Group.objects.get(name='Guessed')
            next_to_guess = Group.objects.get(name='NextToGuess')

            # Obtenemos el juego y el ID de los teams
            game = round.game
            team_ids = game.teams_set.values_list('id', flat=True)

            if first_selection:
                # Si es la primera seleccion, sacamos a todos los usuarios de Guessed y Guessing
                # y agregamos a todos los usuarios a NextToGuess
                guessing.user_set.clear()
                guessed.user_set.clear()
                # Solo para los usuarios que pertenecen al juego actual
                for user_team_pair in UserTeam.objects.filter(team__id__in=team_ids):
                    next_to_guess.user_set.add(user_team_pair.user)
            else:
                # En caso contrario, movemos los usuarios de Guessing a Guessed
                for user in guessing.user_set.all():
                    guessing.user_set.remove(user)
                    guessed.user_set.add(user)

            # Eliminamos las opciones de la seleccion anterior
            Options.objects.all().delete()

            # Movemos los usuarios de group de NextToGuess a Guessing y agregamos
            # sus opciones correspondientes
            for i, user in enumerate(group):
                next_to_guess.user_set.remove(user.user)
                guessing.user_set.add(user.user)
                Options.objects.create(
                    round=round,
                    user=user.user,
                    option1 = options[i][0].user,
                    option2 = options[i][1].user,
                    option3 = options[i][2].user,
                )
        return set_options
    

    def create_selections(self, round, dates, k):
        """ 
        Calcula los grupos por selección y las opciones de adivinanza de los usuarios.
        INPUTS:
            - round: Instancia de Round que indica la ronda actual.
            - dates: Conjunto de fechas en las que se ejecutara cada job.
            * k: Variable que se usa para hacer pruebas.
        """
        ###### EL ARGUMENTO k SOLO SE USA PARA LAS PRUEBAS
        userteam_instances, wolfs, villagers = [], [], []
        # Obtenemos el juego y el ID de los teams
        game = round.game
        team_ids = game.teams_set.values_list('id', flat=True)
        # Obtener los del juego actual
        for user_team_pair in UserTeam.objects.filter(team__id__in=team_ids):
            userteam_instances.append(user_team_pair)
            if user_team_pair.team.name == "Wolfs": wolfs.append(user_team_pair)
            else: villagers.append(user_team_pair)

        # Creamos unos indices con el numero de participantes y los ordenamos aleatoriamente.
        N = len(userteam_instances)
        shuffle(userteam_instances)

        # Calculamos el numero de usuarios que intentaran adivinar por cada seleccion.
        S = [N//6+1 for _ in range(N%6)] + [N//6 for _ in range(6-N%6)]
        groups = []
        for i in range(6):
            groups.append(userteam_instances[sum(S[:i]) : sum(S[:i+1])])
        
        # Creamos las opciones de cada jugador de cada seleccion.
        round_options = []
        for i in range(6):
            i_options = []
            for user_team_pair in groups[i]:
                # Reorganizamos aleatoriamente los lobos y los aldeanos.
                shuffle(wolfs)
                shuffle(villagers)
                # Si el usuario es lobo, tomamos los primeros 3 aldeanos como sus opciones
                if user_team_pair.team.name == "Wolfs": i_options.append(villagers[:3])
                # En caso contrario, tomamos los primeros 3 lobos como sus opciones.
                else: i_options.append(wolfs[:3])
            round_options.append(i_options.copy())

        # Descomentar las siguientes 2 lineas para hacer pruebas
        dates = [datetime.now() + timedelta(seconds=10+k*60) + \
            timedelta(seconds=10*i) for i in range(len(groups))]
        scheduler = BackgroundScheduler()
        for i, group in enumerate(groups):
            # Creamos un job por cada seleccion.
            scheduler.add_job(
                self.get_set_options(group, round, round_options[i], not bool(i)), 
                DateTrigger(dates[i])
            )
        scheduler.start()

    def save(self, commit: bool = True):
        """ Guarda los datos del juego y las rondas en la BD."""

        # CREAMOS LA INSTANCIA DEL JUEGO.
        # Fecha de inicil del juego
        startDate = self.cleaned_data['startDate']
        startDate = datetime(
            year=startDate.year,
            month=startDate.month,
            day=startDate.day
        )
        # Numero de dias que durara el juego
        days = self.cleaned_data['days']
        # Fecha final.
        endDate = startDate + timedelta(days=self.cleaned_data['days'])

        game = Game.objects.create(
            startDate=make_aware(startDate),
            days=self.cleaned_data['days'],
            endDate=make_aware(endDate)
        )
        # game.save()

        # CREAMOS LAS INSTANCIAS DE RONDAS CON SUS RESPECTIVAS SELECCIONES.
        # Aqui almacenaremos las rondas creadas
        rounds = []

        # Ronda 1
        if days in (9, 12): 
            rounds.append(self.gen_round(startDate, 3))
            startDate += timedelta(days=3)
        else:
            rounds.append(self.gen_round(startDate, 2))
            startDate += timedelta(days=2)

        # Ronda 2
        if days in (8, 9, 11, 12): 
            rounds.append(self.gen_round(startDate, 3))
            startDate += timedelta(days=3)
        else:
            rounds.append(self.gen_round(startDate, 2))
            startDate += timedelta(days=2)

        # Ronda 3
        if days in (7, 8, 9): rounds.append(self.gen_round(startDate, 3))
        elif days > 9: rounds.append(self.gen_round(startDate, 6))
        else: rounds.append(self.gen_round(startDate, 2))

        # CREAMOS LOS EQUIPOS
        self.create_teams()

        # SACAMOS A TODOS LOS USUARIOS DE TODOS LOS GRUPOS
        guessing = Group.objects.get(name='Guessing')
        guessed = Group.objects.get(name='Guessed')
        next_to_guess = Group.objects.get(name='NextToGuess')
        guessing.user_set.clear()
        guessed.user_set.clear()
        next_to_guess.user_set.clear()

        # COLOCAMOS TODOS LOS USUARIOS EN NextToGuess
        team_ids = game.teams_set.values_list('id', flat=True)
        for user_team_pair in UserTeam.objects.filter(team__id__in=team_ids):
            next_to_guess.user_set.add(user_team_pair.user)

        # Almacenamos los datos de cada ronda.
        for i, dates in enumerate(rounds):
            round = Round.objects.create(
                game=game,
                firstSelection = r[0],
                secondSelection = r[1],
                thirdSelection = r[2],
                fourthSelection = r[3],
                fifthSelection = r[4],
                sixthSelection = r[5],
            )
            # round.save()
            self.create_selections(round, dates, i)
