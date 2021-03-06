# Generated by Django 3.1.4 on 2020-12-13 19:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('guess', '0013_auto_20201212_2337'),
    ]

    operations = [
        migrations.CreateModel(
            name='Options',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('option1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='option1', to=settings.AUTH_USER_MODEL)),
                ('option2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='option2', to=settings.AUTH_USER_MODEL)),
                ('option3', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='option3', to=settings.AUTH_USER_MODEL)),
                ('round', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='guess.round')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
