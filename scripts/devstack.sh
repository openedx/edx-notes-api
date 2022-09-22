#!/usr/bin/env bash

# Ansible managed

source /edx/app/edx_notes_api/edx_notes_api_env
COMMAND=$1

case $COMMAND in
    start)
        /edx/app/supervisor/venvs/supervisor/bin/supervisord -n --configuration /edx/app/supervisor/conf.d/supervisor.conf
        ;;
    open)
        . /edx/app/edx_notes_api/venvs/edx_notes_api/bin/activate
        cd /edx/app/edx_notes_api/edx_notes_api

        /bin/bash
        ;;
    exec)
        shift

        . /edx/app/edx_notes_api/venvs/edx_notes_api/bin/activate
        cd /edx/app/edx_notes_api/edx_notes_api

        "$@"
        ;;
    *)
        "$@"
        ;;
esac