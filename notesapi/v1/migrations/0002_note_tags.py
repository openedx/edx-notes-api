# -*- coding: utf-8 -*-
""" Add tags field to Note model """

from django.db import migrations, models


class Migration(migrations.Migration):
    """ Add tags field to Note model """

    dependencies = [
        ('v1', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='tags',
            field=models.TextField(default=b'[]', help_text=b'JSON, list of comma-separated tags'),
            preserve_default=True,
        ),
    ]
