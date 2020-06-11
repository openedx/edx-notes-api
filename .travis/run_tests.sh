#!/bin/bash -xe

export DJANGO_SETTINGS_MODULE=notesserver.settings.test

cd /edx/app/edx_notes_api/edx_notes_api

make validate

