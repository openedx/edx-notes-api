FROM ubuntu:focal as app
MAINTAINER devops@edx.org


# Packages installed:
# git; Used to pull in particular requirements from github rather than pypi, 
# and to check the sha of the code checkout.

# ppa:deadsnakes/ppa; since Ubuntu doesn't ship with python 3.8 till 20, we need deadsnakes to install
# python 3.8 on older ubuntu versions

# language-pack-en locales; ubuntu locale support so that system utilities have a consistent
# language and time zone.

# python3.8-dev; to install python 3.8
# python3-venv; installs venv module required to create virtual environments

# libssl-dev; # mysqlclient wont install without this.

# libmysqlclient-dev; to install header files needed to use native C implementation for 
# MySQL-python for performance gains.
# software-properties-common; to get apt-add-repository
# deadsnakes PPA to install Python 3.8
# If you add a package here please include a comment above describing what it is used for

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    apt-add-repository -y ppa:deadsnakes/ppa && \
    apt-get update && apt-get upgrade -qy && \
    apt-get install \
    language-pack-en \
    locales \
    git \
    libmysqlclient-dev \
    libssl-dev \
    build-essential \
    python3.8-dev \
    python3.8-distutils \
    python3.8-venv -qy && \
    rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/edx/app/edx-notes-api/venvs/edx-notes-api
RUN python3.8 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"


RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV EDXNOTES_CONFIG_ROOT /edx/etc
ENV DJANGO_SETTINGS_MODULE notesserver.settings.yaml_config

EXPOSE 8120
RUN useradd -m --shell /bin/false app

WORKDIR /edx/app/notes

# Copy the requirements explicitly even though we copy everything below
# this prevents the image cache from busting unless the dependencies have changed.
COPY requirements/base.txt /edx/app/notes/requirements/base.txt
COPY requirements/pip.txt /edx/app/notes/requirements/pip.txt

# Dependencies are installed as root so they cannot be modified by the application user.
RUN pip install -r requirements/pip.txt
RUN pip install -r requirements/base.txt

RUN mkdir -p /edx/var/log

# Code is owned by root so it cannot be modified by the application user.
# So we copy it before changing users.
USER app

# Gunicorn 19 does not log to stdout or stderr by default. Once we are past gunicorn 19, the logging to STDOUT need not be specified.
CMD gunicorn --workers=2 --name notes -c /edx/app/notes/notesserver/docker_gunicorn_configuration.py --log-file - --max-requests=1000 notesserver.wsgi:application

# This line is after the requirements so that changes to the code will not
# bust the image cache
COPY . /edx/app/notes


FROM app as newrelic
RUN pip install newrelic
CMD newrelic-admin run-program gunicorn --workers=2 --name notes -c /edx/app/notes/notesserver/docker_gunicorn_configuration.py --log-file - --max-requests=1000 notesserver.wsgi:application

