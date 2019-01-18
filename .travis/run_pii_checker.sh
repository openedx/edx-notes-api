#!/bin/bash -xe
. /edx/app/edx_notes_api/venvs/edx_notes_api/bin/activate

export DJANGO_SETTINGS_MODULE=notesserver.settings.test

cd /edx/app/edx_notes_api/edx_notes_api

make pii_check

