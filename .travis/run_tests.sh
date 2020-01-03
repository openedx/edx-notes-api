#!/bin/bash -xe

cd /edx/app/notes

PATH=/home/app/.local/bin:$PATH make validate

