# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/notes/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

ARG BASE_IMAGE_TAG=latest
FROM edxops/focal-common:${BASE_IMAGE_TAG}
LABEL maintainer="edxops"

ARG OPENEDX_RELEASE=master
ENV OPENEDX_RELEASE=${OPENEDX_RELEASE}
ENV NOTES_VERSION=${OPENEDX_RELEASE}
ENV REPO_OWNER=edx


ENV EDX_NOTES_API_VENV="/edx/edx_notes_api/venvs/edx_notes_api"

ADD . /edx/app/edx_ansible/edx_ansible

WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

COPY docker/build/notes/ansible_overrides.yml /
COPY docker/build/notes/edx_notes_api.yml /edx/etc/edx_notes_api.yml


# Ansible Free work start

## tag: install
RUN sudo apt-get update && sudo apt-get -y install python3-dev libmysqlclient-dev python3-virtualenv python3-pip
RUN apt-get install -y sudo
ENV PATH="$EDX_NOTES_API_VENV/bin:$PATH"
RUN pip install -r /edx/edx_notes_api/edx_notes_api/requirements/base.txt
# Copying files
COPY /edx/app/notes/conf_files/edx_notes_api_gunicorn.py /edx/app/edx_notes_api/edx_notes_api_gunicorn.py
COPY edx/app/notes/conf_files/edx_notes_api.sh /edx/app/edx_notes_api/edx_notes_api.sh
COPY /edx/app/notes/conf_files/edx_notes_api.conf /edx/app/supervisor/conf.available.d/edx_notes_api.conf
COPY /edx/app/notes/conf_files/edx_notes_api_env /edx/app/edx_notes_api/edx_notes_api_env
COPY /edx/app/notes/conf_files/edx_notes_api.conf /edx/app/supervisor/conf.d/edx_notes_api.conf
COPY /edx/app/notes/conf_files/manage.edx_notes_api /edx/bin/manage.edx_notes_api

## tag:devstack:install
COPY /edx/app/notes/conf_files/devstack.sh /edx/app/edx_notes_api/devstack.sh

## tag:assets pending/in progress


# Ansible Free work end





# RUN sudo /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook notes.yml \
#     -c local -i '127.0.0.1,' \
#     -t 'install,assets,devstack:install' \
#     --extra-vars="@/ansible_overrides.yml" \
#     --extra-vars="EDX_NOTES_API_VERSION=$NOTES_VERSION" \
#     --extra-vars="COMMON_GIT_PATH=$REPO_OWNER"

USER root
ENTRYPOINT ["/edx/app/edx_notes_api/devstack.sh"]
CMD ["start"]
