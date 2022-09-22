FROM ubuntu:focal as app

# System requirements.
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && \
  apt-get install -qy \ 
  curl \
  vim \
  git-core \
  language-pack-en \
  build-essential \
  python3.8-dev \
  python3-pip \
  python3-virtualenv \
  python3.8-distutils \
  libmysqlclient-dev \
  libssl-dev \
  libcairo2-dev && \
  rm -rf /var/lib/apt/lists/*


# Use UTF-8.
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8



ARG COMMON_APP_DIR="/edx/app"
ARG EDX_NOTES_API_SERVICE_NAME="edx_notes_api"
ENV EDX_NOTES_API_HOME "${COMMON_APP_DIR}/${EDX_NOTES_API_SERVICE_NAME}"
ARG EDX_NOTES_API_APP_DIR="${COMMON_APP_DIR}/${EDX_NOTES_API_SERVICE_NAME}"
ARG SUPERVISOR_APP_DIR="${COMMON_APP_DIR}/supervisor"
ARG EDX_NOTES_API_VENV_DIR="${COMMON_APP_DIR}/${EDX_NOTES_API_SERVICE_NAME}/venvs/${EDX_NOTES_API_SERVICE_NAME}"
ARG SUPERVISOR_VENVS_DIR="${SUPERVISOR_APP_DIR}/venvs"
ARG SUPERVISOR_VENV_DIR="${SUPERVISOR_VENVS_DIR}/supervisor"
ARG EDX_NOTES_API_CODE_DIR="${EDX_NOTES_API_APP_DIR}/${EDX_NOTES_API_SERVICE_NAME}"
ARG SUPERVISOR_AVAILABLE_DIR="${COMMON_APP_DIR}/supervisor/conf.available.d"
ARG SUPERVISOR_VENV_BIN="${SUPERVISOR_VENV_DIR}/bin"
ARG SUPEVISOR_CTL="${SUPERVISOR_VENV_BIN}/supervisorctl"
ARG SUPERVISOR_VERSION="4.2.1"
ARG SUPERVISOR_CFG_DIR="${SUPERVISOR_APP_DIR}/conf.d"


ENV HOME /root
ENV PATH "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin"
ENV PATH "${EDX_NOTES_API_VENV_DIR}/bin:$PATH"
ENV COMMON_CFG_DIR "/edx/etc"
ENV EDX_NOTES_API_CFG_DIR "${COMMON_CFG_DIR}/edx_notes_api"
ENV EDX_NOTES_API_CFG "/edx/etc/edx_notes_api.yml"

RUN addgroup edx_notes_api
RUN adduser --disabled-login --disabled-password edx_notes_api --ingroup edx_notes_api


# Make necessary directories and environment variables.
RUN mkdir -p /edx/var/edx_notes_api/staticfiles
RUN mkdir -p /edx/var/edx_notes_api/media
# Log dir
RUN mkdir /edx/var/log/

RUN virtualenv -p python3.8 --always-copy ${EDX_NOTES_API_VENV_DIR}
RUN virtualenv -p python3.8 --always-copy ${SUPERVISOR_VENV_DIR}

#install supervisor and deps in its virtualenv
RUN . ${SUPERVISOR_VENV_BIN}/activate && \
  pip install supervisor==${SUPERVISOR_VERSION} backoff==1.4.3 boto==2.48.0 && \
  deactivate

COPY requirements/base.txt ${EDX_NOTES_API_CODE_DIR}/requirements/base.txt

RUN pip install -r ${EDX_NOTES_API_CODE_DIR}/requirements/base.txt

# Working directory will be root of repo.
WORKDIR ${EDX_NOTES_API_CODE_DIR}

# Copy over rest of code.
# We do this AFTER requirements so that the requirements cache isn't busted
# every time any bit of code is changed.
COPY . .
COPY /configuration_files/edx_notes_api_gunicorn.py ${EDX_NOTES_API_HOME}/edx_notes_api_gunicorn.py
# COPY /configuration_files/discovery-workers.sh ${DISCOVERY_HOME}/discovery-workers.sh
# COPY /configuration_files/discovery.yml ${DISCOVERY_CFG}
COPY /scripts/edx_notes_api.sh ${EDX_NOTES_API_HOME}/edx_notes_api.sh
# COPY /configuration_files/supervisor.conf ${SUPERVISOR_APP_DIR}/supervisord.conf
# create supervisor job
COPY /configuration_files/supervisor.service /etc/systemd/system/supervisor.service
COPY /configuration_files/supervisor.conf ${SUPERVISOR_CFG_DIR}/supervisor.conf
COPY /configuration_files/supervisorctl ${SUPERVISOR_VENV_BIN}/supervisorctl
# Manage.py symlink
COPY /manage.py /edx/bin/manage.edx_notes_api

# Expose canonical Discovery port
EXPOSE 18281

FROM app as prod

ENV DJANGO_SETTINGS_MODULE "notesserver.settings.dev"

RUN make static

ENTRYPOINT ["/edx/app/edx_notes_api/edx_notes_api.sh"]

FROM app as dev

ENV DJANGO_SETTINGS_MODULE "notesserver.settings.devstack"

RUN pip install -r ${EDX_NOTES_API_CODE_DIR}/requirements/base.txt

COPY /scripts/devstack.sh ${EDX_NOTES_API_HOME}/devstack.sh

RUN chown edx_notes_api:edx_notes_api /edx/app/edx_notes_api/devstack.sh && chmod a+x /edx/app/edx_notes_api/devstack.sh

# Devstack related step for backwards compatibility
RUN touch /edx/app/${EDX_NOTES_API_SERVICE_NAME}/${EDX_NOTES_API_SERVICE_NAME}_env

ENTRYPOINT ["/edx/app/edx_notes_api/devstack.sh"]
CMD ["start"]