# Generated by Django 5.1.7 on 2025-04-04 13:41

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_remove_studentrecord_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='studentrecord',
            name='initial_password',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='studentrecord',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='studentrecord',
            name='username',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
