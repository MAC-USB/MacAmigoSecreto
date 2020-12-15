from guess.forms import *

for i in range(24):
    user = User.objects.create_user(
        username="player" + str(i),
        email='',
        password="ladilla1.",
        first_name="Player",
        last_name=str(i)
    )
    user.save()
    UserData(
        user=user,
        alias="PL" + str(i),
        gift="Titulo del player " + str(i),
    ).save()