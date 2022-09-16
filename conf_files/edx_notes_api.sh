#!/usr/bin/env bash

# Ansible managed


source /edx/app/edx_notes_api/edx_notes_api_env

export PID=/var/tmp/edx_notes_api.pid
export PORT=8120
export ADDRESS=0.0.0.0

# We exec so that gunicorn is the child of supervisor and can be managed properly
exec /edx/app/edx_notes_api/venvs/edx_notes_api/bin/gunicorn -c /edx/app/edx_notes_api/edx_notes_api_gunicorn.py  notesserver.wsgi:application
