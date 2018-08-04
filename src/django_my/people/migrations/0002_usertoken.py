# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-12-03 10:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserToken',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('key', models.CharField(max_length=40, primary_key=True, serialize=False, verbose_name='token')),
                ('device_uuid', models.CharField(blank=True, max_length=60, null=True, verbose_name='device uuid')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auth_tokens', to='people.CustomUser', verbose_name='user')),
            ],
            options={
                'verbose_name': 'user token',
                'verbose_name_plural': 'user tokens',
            },
        ),
    ]