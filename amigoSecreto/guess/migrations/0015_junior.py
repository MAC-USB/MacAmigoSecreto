# Generated by Django 3.1.4 on 2020-12-18 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guess', '0014_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='Junior',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('sound', models.FileField(upload_to='')),
                ('photo', models.FileField(upload_to='')),
            ],
        ),
    ]
