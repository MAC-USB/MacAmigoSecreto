# Generated by Django 3.1.4 on 2020-12-10 22:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('guess', '0009_auto_20201210_2042'),
    ]

    operations = [
        migrations.CreateModel(
            name='Round',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('firstSelection', models.DateTimeField()),
                ('secondSelection', models.DateTimeField()),
                ('thirdSelection', models.DateTimeField()),
                ('fourthSelection', models.DateTimeField()),
                ('fifthSelection', models.DateTimeField()),
                ('sixthSelection', models.DateTimeField()),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='guess.game')),
            ],
        ),
    ]
