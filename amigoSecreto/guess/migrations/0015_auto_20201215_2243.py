# Generated by Django 3.1.4 on 2020-12-15 22:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guess', '0014_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='guess',
            name='date',
            field=models.DateTimeField(),
        ),
    ]
