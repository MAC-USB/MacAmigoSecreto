# Generated by Django 3.1.4 on 2020-12-12 23:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guess', '0011_auto_20201212_1920'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teams',
            name='score',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]