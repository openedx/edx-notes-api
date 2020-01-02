#!/bin/bash -xe

export DJANGO_SETTINGS_MODULE=notesserver.settings.test

cd /edx/app/notes

make pii_check

