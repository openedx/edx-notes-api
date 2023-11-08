FROM ubuntu:focal as app

# Packages installed:
# git; Used to pull in particular requirements from github rather than pypi, 
# and to check the sha of the code checkout.

# language-pack-en locales; ubuntu locale support so that system utilities have a consistent
# language and time zone.

# python3.8-dev; to install python 3.8
# python3-venv; installs venv module required to create virtual environments

# libssl-dev; # mysqlclient wont install without this.

# libmysqlclient-dev; to install header files needed to use native C implementation for 
# MySQL-python for performance gains.

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
    pkg-config \
    libssl-dev \
    build-essential \
    python3.8-dev \
    python3.8-distutils \
    python3-virtualenv -qy && \
    rm -rf /var/lib/apt/lists/*


RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8


# ENV variables lifetime is bound to the container whereas ARGS variables lifetime is bound to the image building process only
# Also ARGS provide us an option of compatibility of Path structure for Tutor and other OpenedX installations
ARG COMMON_CFG_DIR "/edx/etc"
ARG COMMON_APP_DIR="/edx/app"
ARG NOTES_APP_DIR="${COMMON_APP_DIR}/notes"
ARG NOTES_VENV_DIR="${COMMON_APP_DIR}/venvs/notes"

ENV NOTES_APP_DIR ${NOTES_APP_DIR}
ENV PATH="$NOTES_VENV_DIR/bin:$PATH"

RUN useradd -m --shell /bin/false app

RUN virtualenv -p python3.8 --always-copy ${NOTES_VENV_DIR}

COPY requirements ${NOTES_APP_DIR}/requirements

WORKDIR ${NOTES_APP_DIR}

# edx_notes_api service config commands below
RUN pip install --no-cache-dir -r ${NOTES_APP_DIR}/requirements/base.txt
RUN pip install --no-cache-dir -r ${NOTES_APP_DIR}/requirements/pip.txt

RUN mkdir -p /edx/var/log

COPY . ${NOTES_APP_DIR}

EXPOSE 8120

FROM app as dev

ENV DJANGO_SETTINGS_MODULE "notesserver.settings.devstack"

# Backwards compatibility with devstack
RUN touch "${COMMON_APP_DIR}/edx_notes_api_env" 

CMD while true; do python ./manage.py runserver 0.0.0.0:8120; sleep 2; done

FROM app as production

ENV EDXNOTES_CONFIG_ROOT /edx/etc
ENV DJANGO_SETTINGS_MODULE "notesserver.settings.yaml_config"

COPY edx_notes_api.yml "/edx/etc/edx_notes_api.yml"

# Code is owned by root so it cannot be modified by the application user.
# So we copy it before changing users.
USER app

# RUN python manage.py migrate

# Gunicorn 19 does not log to stdout or stderr by default. Once we are past gunicorn 19, the logging to STDOUT need not be specified.
# CMD gunicorn --workers=2 --name notes -c /edx/app/notes/notesserver/docker_gunicorn_configuration.py --log-file - --max-requests=1000 notesserver.wsgi:application
CMD newrelic-admin run-program gunicorn --workers=2 --name notes -c /edx/app/notes/notesserver/docker_gunicorn_configuration.py --log-file - --max-requests=1000 notesserver.wsgi:application