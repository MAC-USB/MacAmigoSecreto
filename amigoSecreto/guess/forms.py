""" guess Forms. """

# Forms de Django.
from django import forms
from django.contrib.auth.forms import UserCreationForm

# Modelos de Django.
from django.contrib.auth.models import User, Group

# Validadores de Django.
from django.core.exceptions import ValidationError

# Utilidades de Django.
from django.utils.timezone import make_aware

# Scheduler.
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

# Nuestros modelos.
from .models import Game, UserData, Teams, GivesTo, UserTeam, Guess, Round, Options

# Utilidades.
from random import shuffle, choices
from datetime import date, datetime, timedelta

class SignUpForm(UserCreationForm):
    """ 
    Clase heredada de UserCreationFrom para registrar usuarios.
    Campos: 
        - first_name
        - last_name
        - username
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
        """ Indicamos el modelo a usar y los campos del form para el registro. """
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
        first_name = self.cleaned_data['first_name']
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        return last_name

    def clean_username(self):
        """ Verificamos que el username no esta en uso."""
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists")
        return username

    def clean_alias(self):
        """ Verificamos que el alias no esta en uso."""
        alias = self.cleaned_data['alias']
        if UserData.objects.filter(alias=alias).exists():
            raise ValidationError("Alias already exists")
        return alias

    def clean_gift(self):
        gift = self.cleaned_data['gift']
        return gift

    def clean_password2(self):
        """ Verifica que ambas contrasenyas coinciden."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError("Password don't match")
        return password2

    def save(self, commit: bool = True):
        """ Guarda los datos del usuario en la BD usando los modelos
        User y UserData."""
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
        - days: Numero de juegos que durara el juego. Debe tener un valor entre
            6 y 12, incluyendo ambas.
    """
    startDate = forms.DateField(initial=date.today() + timedelta(days=1))
    days = forms.IntegerField(min_value=6, max_value=12)

    class Meta:
        """ Indicamos el modelo a usar y los campos del form para la 
        creacion del juego. """
        model = Game
        fields = (
            'startDate',
            'days',
        )

    def clean_startDate(self):
        """ Verificamos que la fecha de inicio sea al menos el dia siguiente."""
        startDate = self.cleaned_data['startDate']
        if startDate <= date.today():
            raise forms.ValidationError('The date must be at least tomorrow.')
        return startDate

    def clean_days(self):
        days = self.cleaned_data['days']
        return days

    def gen_round(self, startDate, days):
        """ 
        Genera las fechas de las selecciones de una ronda segun su fecha de inicio
        y el tiempo que durara.

        INPUTS:
            - startDate: Fecha de inicio de la ronda.
            - days: Numero de dias que durara la ronda.
        """
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
        creando las instancias de Team y UserTeam correspondientes. Luego crea
        las instancias de GivesTo correspondientes, las cuales representan la
        relacion 'X le regala a Y'."""
        # Almacenamos la instancia de todos los jugadores
        users = list(UserData.objects.all())

        # Creamos unos indices con el numero de participantes y los ordenamos aleatoriamente.
        N = len(users)
        indexes = [i for i in range(N)]
        shuffle(indexes)

        # Separamos en lobos y aldeanos.
        wolfs = [users[i] for i in indexes[:N//2]]
        villagers = [users[i] for i in indexes[N//2:]]

        # El último juego creado es el activo
        game = Game.objects.latest('startDate')

        # Creamos las instancias de UserTeam para el equipo lobo.
        wolfs_team = Teams.objects.get_or_create(game=game, name='Wolfs')[0]#, score=0)
        for wolf in wolfs:
            UserTeam.objects.create(team=wolfs_team, user=wolf.user)

        # Creamos las instancias de UserTeam para el equipo aldeano.
        villagers_team = Teams.objects.get_or_create(game=game, name='Villagers')[0]#, score=0)
        for villager in villagers:
            UserTeam.objects.create(team=villagers_team, user=villager.user)

        ##### ------------ REPRESENTACION DEL POTE DE EAS ------------ #####
        # Creamos las instancias de GivesTo.
        shuffle(wolfs)
        shuffle(villagers)
        for i in range(len(wolfs)):
            GivesTo.objects.create(game=game, gifter=wolfs[i].user, gifted=villagers[i].user)
        shuffle(wolfs)
        shuffle(villagers)
        for i in range(len(wolfs)):
            GivesTo.objects.create(game=game, gifted=wolfs[i].user, gifter=villagers[i].user)

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
    
    def create_selections(self, round, dates):
        """ 
        Calcula los grupos por selección y las opciones de adivinanza de los usuarios.
        INPUTS:
            - round: Instancia de Round que indica la ronda actual.
            - dates: Conjunto de fechas en las que se ejecutara cada job.
        """
        # Obtenemos el juego y el ID de los teams
        game = round.game
        team_ids = game.teams_set.values_list('id', flat=True)

        # Almacenaremos los usuarios, los lobos y los aldeanos respectivamente.
        userteam_instances, wolfs, villagers = [], [], []
        # Obtenemos los usuarios del juego actual
        for user_team_pair in UserTeam.objects.filter(team__id__in=team_ids):
            userteam_instances.append(user_team_pair)
            # Ademas los separamos en lobos y aldeanos
            if user_team_pair.team.name == "Wolfs": wolfs.append(user_team_pair)
            else: villagers.append(user_team_pair)

        # Ordenamos aleatoriamente los usuarios.
        N = len(userteam_instances)
        shuffle(userteam_instances)

        # Calculamos el numero de usuarios que intentaran adivinar por cada seleccion,
        # tratando de ser lo mas equitativo posible,
        S = [N//6+1 for _ in range(N%6)] + [N//6 for _ in range(6-N%6)]
        groups = []
        for i in range(6): groups.append(userteam_instances[sum(S[:i]) : sum(S[:i+1])])
        
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

        # Creamos los jobs correspondientes a cada seleccion.
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
        # Fecha de inicial del juego
        startDate = self.cleaned_data['startDate']
        startDate = datetime(
            year=startDate.year,
            month=startDate.month,
            day=startDate.day
        )
        # Numero de dias que durara el juego
        days = self.cleaned_data['days']
        # Fecha del final de la fase de adivinanzas.
        endDate = startDate + timedelta(days=self.cleaned_data['days'])
        # Creamos la instancia del juego.
        game = Game.objects.create(
            startDate=make_aware(startDate),
            days=self.cleaned_data['days'],
            endDate=make_aware(endDate)
        )
        game.save()

        # Creamos las fechas de seleccion de cada ronda,
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

        # Creamos los equipos
        self.create_teams()

        # Sacamos a los usuarios de todos los grupos.
        guessing = Group.objects.get(name='Guessing')
        guessed = Group.objects.get(name='Guessed')
        next_to_guess = Group.objects.get(name='NextToGuess')
        guessing.user_set.clear()
        guessed.user_set.clear()
        next_to_guess.user_set.clear()
        # Colocamos todos los usuarios en NextToGuess
        team_ids = game.teams_set.values_list('id', flat=True)
        for user_team_pair in UserTeam.objects.filter(team__id__in=team_ids):
            next_to_guess.user_set.add(user_team_pair.user)

        # Almacenamos los datos de cada ronda.
        for dates in rounds:
            round = Round.objects.create(
                game=game,
                firstSelection = dates[0],
                secondSelection = dates[1],
                thirdSelection = dates[2],
                fourthSelection = dates[3],
                fifthSelection = dates[4],
                sixthSelection = dates[5],
            )
            # round.save()
            self.create_selections(round, dates)

class GuessForm(forms.ModelForm):
    """ 
    Clase heredada de forms.ModelForm para crear instancias de adivinanzas.
    Campos: 
        - gifter: Usuario que entrega el regalo.
        - gifted: Usuario que recibe el regalo.
    """
    def __init__(self, *args, **kwargs):
        super(GuessForm, self).__init__(*args, **kwargs)

        # Obtenemos los datos del usuario en sesion.
        self.user = kwargs.pop('user')
        # El último juego creado es el activo.
        game = Game.objects.latest('startDate')
        team = UserTeam.objects.filter(user=self.user)[0].team 

        # Si no nos encontramos en la fase del dia de juego.
        if not game.gameDay:
            # Obtenemos las opciones del jugador para elegir a quien adivinar.
            gifter_options = Options.objects.filter(user=self.user)[0]
            # Obtenemos los UserData de cada opcion
            gifter_options = [
                UserData.objects.filter(user=gifter_options.option1)[0],
                UserData.objects.filter(user=gifter_options.option2)[0],
                UserData.objects.filter(user=gifter_options.option3)[0]
            ]
            # Colocaremos los aliases en vez de los usernames.
            gifter_options = [(user_data.alias, user_data.alias) for user_data in gifter_options]

            # Colocamos todos los jugadores como opcion de gifted.
            gifted_options = list(UserTeam.objects.all())
            # Obtenemos los UserData de cada jugador.
            gifted_options = [UserData.objects.filter(user=user_team.user)[0] for user_team in gifted_options]
            # Colocaremos los aliases en vez de los usernames
            gifted_options = [(user_data.alias, user_data.alias) for user_data in gifted_options]

        # En cambio, si nos encontramos en la fase de dia del juego.
        else:
            # Las opciones de gifter seran todos los usuarios del equipo contrario.
            gifter_options = []
            for user_team in UserTeam.objects.all():
                if user_team.team != team:
                    gifter_options.append(UserData.objects.filter(user=user_team.user)[0])
            # Colocaremos los aliases en vez de los usernames.
            gifter_options = [(user_data.alias, user_data.alias) for user_data in gifter_options]

            # La unica opcion de gifted sera el usuario registrado.
            alias = UserData.objects.filter(user=self.user)[0]
            gifted_options = [(alias, alias)]

        # Colocamos las opciones.
        self.fields['gifter'] = forms.ChoiceField(choices=gifter_options)
        self.fields['gifted'] = forms.ChoiceField(choices=gifted_options)

    class Meta:
        """ Indicamos el modelo a usar y los campos del form para la 
        creacion del guess. """
        model = Guess
        fields = (
            'gifter',
            'gifted',
        )

    def clean_gifter(self):
        """Dado el alias que el owner indico como gifter, obtenemos el User asociado. """
        gifter = self.cleaned_data['gifter']
        gifter = UserData.objects.filter(alias=gifter)[0]
        return gifter.user

    def clean_gifted(self):
        """Dado el alias que el owner indico como gifted, obtenemos el User asociado. """
        gifted = self.cleaned_data['gifted']
        gifted = UserData.objects.filter(alias=gifted)[0]
        return gifted.user

    def save(self, commit: bool = True):
        """ Guarda los datos del guess en la BD."""
        # El último juego creado es el activo
        game = Game.objects.latest('startDate')

        # El owner sera el jugador registrado
        owner = self.user
        # Obtenemos el gifter y el gifted
        gifter = self.cleaned_data['gifter']
        gifted = self.cleaned_data['gifted']

        # Si no estamos en la fase de dia del juego.
        if not game.gameDay:
            # Obtenemos la respuesta
            if GivesTo.objects.filter(gifter=gifter)[0].gifted == gifted: 
                # Si adivino correctamente, la respuesta sera True
                answer=True
            else:
                # En caso contrario habra una posibilidad de 5/N (siendo N el numero
                # de jugadores) de que de un falso positivo.
                N = len(UserTeam.objects.all())
                answer = choices([True, False], weights=[5/N, 1 - 5/N], k=1)[0]

            # Creamos una instancia de Guess
            Guess.objects.create(
                game=game,
                owner=owner,
                gifter=gifter,
                gifted=gifted,
                date=make_aware(datetime.now()),
                answer=answer
            ).save()

            # Movemos al owner del grupo Guessing a Guessed
            Group.objects.get(name='Guessing').user_set.remove(owner)
            Group.objects.get(name='Guessed').user_set.add(owner)

            # Eliminamos las opciones del owner
            Options.objects.filter(user=owner).delete()

        # En cambio, si estamos en la fase de dia del juego.
        else:
            # Verificamo si adivino correctamente
            answer = GivesTo.objects.filter(gifter=gifter)[0].gifted == gifted
            owner_data = UserData.objects.filter(user=self.user)[0]
            owner_data.guessed = answer
            owner_data.save()

            # Aumentamos el score de su equipo
            team = UserTeam.objects.filter(user=self.user)[0].team 
            team.score += 1
            team.save()

            # Movemos al owner del grupo Guessing a Guessed (si respondio correctamente)
            # o a NextToGuess (si respondi0 incorrectamente)
            Group.objects.get(name='Guessing').user_set.remove(self.user)
            if answer: Group.objects.get(name='Guessed').user_set.add(self.user)
            else: Group.objects.get(name='NextToGuess').user_set.add(self.user)

            # Obtenemos los usuario del equipo contrario
            another_team = []
            for user_team in UserTeam.objects.all():
                if user_team.team != team:
                    another_team.append(UserData.objects.filter(user=user_team.user)[0])

            # Ordenamos aleatoriamente dicho equipo
            shuffle(another_team)

            # La siguiente persona en adivinar sera el primer que aparezca del siguiente 
            # equipo que aun no haya adivinado quien le regala
            for user_data in another_team:
                if not user_data.guessed:
                    Group.objects.get(name='NextToGuess').user_set.remove(user_data.user)
                    Group.objects.get(name='Guessing').user_set.add(user_data.user)
                    return

            # Si llegamos hasta aca, significa que el otro equipo ya gano.
            # Obtenemos los usuario de este equipo
            owner_team = []
            for user_team in UserTeam.objects.all():
                if user_team.team == team:
                    owner_team.append(UserData.objects.filter(user=user_team.user)[0])

            # Ordenamos aleatoriamente dicho equipo
            shuffle(owner_team)

            # La siguiente persona en adivinar sera el primer que aparezca del siguiente 
            # equipo que aun no haya adivinado quien le regala
            for user_data in owner_team:
                if not user_data.guessed:
                    Group.objects.get(name='NextToGuess').user_set.remove(user_data.user)
                    Group.objects.get(name='Guessing').user_set.add(user_data.user)
                    return

            # Si llegamos hasta aca, significa que ya finalizo el juego.
            game.end = True
            game.save()
                     
class StartGameForm(forms.Form):
    """ 
    Clase heredada de forms.ModelForm para pasar un juego a la fase del dia de juego.
    Campos: 
        - choice: Mas que todo para verificar que el usuario quiere iniciar la fase
            del dia de juego. Solo hay dos opciones: Si y No.
    """
    def __init__(self, *args, **kwargs):
        super(StartGameForm, self).__init__(*args, **kwargs)

        # El último juego creado es el activo
        self.game = Game.objects.latest('startDate')
        self.text = "Do you want to start the " + str(self.game)
        self.fields[self.text] = forms.TypedChoiceField(
            choices=((False, 'No'), (True, 'Yes'))
        )

    def save(self, commit: bool = True):
        """ Actualiza los datos del juego en la BD."""
        if self.cleaned_data[self.text]:
            # Obtenemos los 3 grupos
            guessing = Group.objects.get(name='Guessing')
            guessed = Group.objects.get(name='Guessed')
            next_to_guess = Group.objects.get(name='NextToGuess')
            
            # Obtenemos los ids de los equipos
            team_ids = self.game.teams_set.values_list('id', flat=True)

            # Sacamos a todos los usuarios de Guessed y Guessing
            # y agregamos a todos los usuarios a NextToGuess
            guessing.user_set.clear()
            guessed.user_set.clear()
            # Solo para los usuarios que pertenecen al juego actual
            for user_team_pair in UserTeam.objects.filter(team__id__in=team_ids):
                next_to_guess.user_set.add(user_team_pair.user)

            # Indicamos que el juego actual esta en fase de dia del juego.
            self.game.gameDay = True
            self.game.save()

            # Elegimos aleatoriamente a un usuario para adivinar
            users = [user for user in UserData.objects.all()]
            shuffle(users)
            # Y los pasamos del grupo NextToGuess a Guessing.
            Group.objects.get(name='NextToGuess').user_set.remove(users[0].user)
            Group.objects.get(name='Guessing').user_set.add(users[0].user)
