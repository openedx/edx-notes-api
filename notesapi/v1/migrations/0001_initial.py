# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import notesapi.v1.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_id', models.CharField(max_length=255)),
                ('course_id', notesapi.v1.models.CourseKeyField(max_length=255)),
                ('usage_id', notesapi.v1.models.UsageKeyField(max_length=255)),
                ('text', models.TextField(default=b'')),
                ('quote', models.TextField(default=b'')),
                ('range_start', models.CharField(max_length=2048)),
                ('range_start_offset', models.IntegerField()),
                ('range_end', models.CharField(max_length=2048)),
                ('range_end_offset', models.IntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
