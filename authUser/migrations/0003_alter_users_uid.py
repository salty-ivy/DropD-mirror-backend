# Generated by Django 4.0.2 on 2022-09-05 15:08

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('authUser', '0002_remove_users_is_completed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='users',
            name='uid',
            field=models.CharField(db_index=True, default=uuid.uuid4, max_length=255, unique=True),
        ),
    ]
