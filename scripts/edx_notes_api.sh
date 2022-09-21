#!/usr/bin/env bash


export EDX_REST_API_CLIENT_NAME="default_env-default_deployment-edx_notes_api"

exec /edx/app/edx_notes_api/venvs/edx_notes_api/bin/gunicorn -c /edx/app/edx_notes_api/edx_notes_api_gunicorn.py --reload notesserver.wsgi:application