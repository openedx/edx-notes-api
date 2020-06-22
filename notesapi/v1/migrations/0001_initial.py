# -*- coding: utf-8 -*-
""" Initial migration file for creating Note model """

from django.db import migrations, models


class Migration(migrations.Migration):
    """ Initial migration file for creating Note model """

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_id', models.CharField(
                    help_text=b'Anonymized user id, not course specific', max_length=255, db_index=True
                )),
                ('course_id', models.CharField(max_length=255, db_index=True)),
                ('usage_id', models.CharField(help_text=b'ID of XBlock where the text comes from', max_length=255)),
                ('quote', models.TextField(default=b'')),
                ('text', models.TextField(default=b'', help_text=b"Student's thoughts on the quote", blank=True)),
                ('ranges', models.TextField(help_text=b'JSON, describes position of quote in the source text')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
