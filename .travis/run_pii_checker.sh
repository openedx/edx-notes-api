#!/bin/bash -xe

export DJANGO_SETTINGS_MODULE=notesserver.settings.test

cd /edx/app/notes

PATH=/home/app/.local/bin:$PATH make pii_check

