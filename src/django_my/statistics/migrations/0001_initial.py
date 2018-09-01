# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2018-09-01 19:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('order', '0001_initial'),
        ('people', '0005_auto_20180901_1914'),
    ]

    operations = [
        migrations.CreateModel(
            name='DownloadStatistics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('click_count', models.PositiveIntegerField(default=0, verbose_name='\u70b9\u51fb\u91cf')),
                ('visitor_count', models.PositiveIntegerField(default=0, verbose_name='\u8bbf\u5ba2\u91cf')),
                ('date', models.DateField(verbose_name='\u65e5\u671f')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.CustomUser', verbose_name='\u7528\u6237')),
            ],
            options={
                'verbose_name': 'APP\u8bbf\u95ee\u7edf\u8ba1',
                'verbose_name_plural': 'APP\u8bbf\u95ee\u7edf\u8ba1',
            },
        ),
        migrations.CreateModel(
            name='Statistics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveSmallIntegerField(default=0, verbose_name='\u5e74')),
                ('month', models.PositiveSmallIntegerField(default=0, verbose_name='\u6708')),
                ('day', models.PositiveSmallIntegerField(default=0, verbose_name='\u65e5')),
                ('viewed_count', models.PositiveIntegerField(default=0, verbose_name='\u6d4f\u89c8\u91cf')),
                ('download_count', models.PositiveIntegerField(default=0, verbose_name='\u4e0b\u8f7d\u91cf')),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u4e8e')),
                ('dt_updated', models.DateTimeField(auto_now=True, verbose_name='\u66f4\u65b0\u4e8e')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='order.PurchaseItem', verbose_name='\u8d2d\u4e70\u9879\u76ee')),
            ],
            options={
                'verbose_name': 'H5\u8bbf\u95ee\u7edf\u8ba1',
                'verbose_name_plural': 'H5\u8bbf\u95ee\u7edf\u8ba1',
            },
        ),
        migrations.CreateModel(
            name='VisitIP',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.GenericIPAddressField(verbose_name='\u8bbf\u95eeIP')),
                ('user_agent', models.CharField(blank=True, max_length=500, null=True, verbose_name='\u8bbf\u95eeAgent')),
                ('date', models.DateField(verbose_name='\u65e5\u671f')),
                ('download_data', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='statistics.DownloadStatistics', verbose_name='\u4e0b\u8f7d\u7edf\u8ba1')),
            ],
            options={
                'verbose_name': '\u8bbf\u95eeIP',
                'verbose_name_plural': '\u8bbf\u95eeIP',
            },
        ),
    ]