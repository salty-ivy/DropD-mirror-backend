# Generated by Django 4.0.2 on 2022-07-09 07:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authUser', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='users',
            name='is_completed',
        ),
    ]
