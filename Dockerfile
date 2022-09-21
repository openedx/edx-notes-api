FROM ubuntu:focal as app
LABEL maintainer="edxops"

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
  python3-virtualenv \
  python3.8-distutils \
  libmysqlclient-dev \
  libssl-dev \
  libcairo2-dev && \
  rm -rf /var/lib/apt/lists/*

ARG OPENEDX_RELEASE=master
ARG COMMON_APP_DIR="/edx/app"
ARG EDX_NOTES_API_SERVICE_NAME="edx_notes_api"
ARG EDX_NOTES_API_APP_DIR="${COMMON_APP_DIR}/${EDX_NOTES_API_SERVICE_NAME}"
ARG EDX_NOTES_API_CODE_DIR="${EDX_NOTES_API_APP_DIR}/${EDX_NOTES_API_SERVICE_NAME}"
ARG EDX_NOTES_API_VENV_DIR="${COMMON_APP_DIR}/${EDX_NOTES_API_SERVICE_NAME}/venvs/${EDX_NOTES_API_SERVICE_NAME}"
ARG SUPERVISOR_APP_DIR="${COMMON_APP_DIR}/supervisor"
ARG SUPERVISOR_AVAILABLE_DIR="${COMMON_APP_DIR}/supervisor/conf.available.d"
ARG SUPERVISOR_CFG_DIR="${SUPERVISOR_APP_DIR}/conf.d"
ARG SUPERVISOR_VENVS_DIR="${SUPERVISOR_APP_DIR}/venvs"
ARG SUPERVISOR_VENV_DIR="${SUPERVISOR_VENVS_DIR}/supervisor"
ARG SUPERVISOR_VENV_BIN="${SUPERVISOR_VENV_DIR}/bin"
ARG SUPERVISOR_VERSION="4.2.1"


ENV OPENEDX_RELEASE=${OPENEDX_RELEASE}
ENV NOTES_VERSION=${OPENEDX_RELEASE}
ENV REPO_OWNER=edx
ENV HOME /root
RUN addgroup edx_notes_api
RUN adduser --disabled-login --disabled-password edx_notes_api --ingroup edx_notes_api
ENV EDX_NOTES_API_HOME "${COMMON_APP_DIR}/${EDX_NOTES_API_SERVICE_NAME}"
ENV PATH "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin"
ENV PATH="$EDX_NOTES_API_VENV_DIR/bin:$PATH"


RUN virtualenv -p python3.8 --always-copy ${EDX_NOTES_API_VENV_DIR}
RUN virtualenv -p python3.8 --always-copy ${SUPERVISOR_VENV_DIR}


#install supervisor and deps in its virtualenv
RUN . ${SUPERVISOR_VENV_BIN}/activate && \
  pip install supervisor==${SUPERVISOR_VERSION} backoff==1.4.3 boto==2.48.0 && \
  deactivate

COPY requirements/base.txt ${EDX_NOTES_API_CODE_DIR}/requirements/base.txt
RUN pip install -r ${EDX_NOTES_API_CODE_DIR}/requirements/base.txt

# RUN sudo apt-get update && sudo apt-get -y install python3-dev libmysqlclient-dev python3-virtualenv python3-pip
ENV PATH="$EDX_NOTES_API_VENV/bin:$PATH"

# Working directory will be root of repo.
WORKDIR ${EDX_NOTES_API_CODE_DIR}

# Copy over rest of code.
# We do this AFTER requirements so that the requirements cache isn't busted
# every time any bit of code is changed.
COPY . .

# Copying files
COPY /configuration_files/edx_notes_api_gunicorn.py ${EDX_NOTES_API_HOME}/edx_notes_api_gunicorn.py
COPY /scripts/edx_notes_api.sh ${EDX_NOTES_API_HOME}/edx_notes_api.sh
COPY /configuration_files/supervisor.conf ${SUPERVISOR_APP_DIR}/supervisord.conf
COPY /manage.py /edx/bin/manage.edx_notes_api


# create supervisor job
COPY /configuration_files/supervisor.service /etc/systemd/system/supervisor.service
COPY /configuration_files/supervisor.conf ${SUPERVISOR_CFG_DIR}/supervisor.conf
COPY /configuration_files/supervisorctl ${SUPERVISOR_VENV_BIN}/supervisorctl







EXPOSE 18281

FROM app as prod

ENV DJANGO_SETTINGS_MODULE "notesserver.settings.dev"

RUN make static

ENTRYPOINT ["/edx/app/edx_notes_api/edx_notes_api.sh"]

FROM app as dev

ENV DJANGO_SETTINGS_MODULE "notesserver.settings.dev"

RUN pip install -r ${EDX_NOTES_API_CODE_DIR}/requirements/base.txt

COPY /scripts/devstack.sh ${EDX_NOTES_API_HOME}/devstack.sh

RUN chown edx_notes_api:edx_notes_api /edx/app/edx_notes_api/devstack.sh && chmod a+x /edx/app/edx_notes_api/devstack.sh

# Devstack related step for backwards compatibility
RUN touch /edx/app/${EDX_NOTES_API_SERVICE_NAME}/${EDX_NOTES_API_SERVICE_NAME}_env




ENTRYPOINT ["/edx/app/edx_notes_api/devstack.sh"]
CMD ["start"]
