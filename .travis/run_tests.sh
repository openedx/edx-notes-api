#!/bin/bash -xe
. /edx/app/edx_notes_api/venvs/edx_notes_api/bin/activate

cd /edx/app/edx_notes_api/edx_notes_api

make validate

