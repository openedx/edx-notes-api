FROM ubuntu:bionic
MAINTAINER devops@edx.org

RUN apt-get update && apt-get upgrade -qy && apt-get install language-pack-en locales git python2.7 python-pip libmysqlclient-dev -qy && \
pip install --upgrade pip setuptools && \
rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV EDXNOTES_CONFIG_ROOT /edx/app
ENV DJANGO_SETTINGS_MODULE notesserver.settings.yaml_config

EXPOSE 8000
RUN useradd -m --shell /bin/false app

WORKDIR /edx/notes
COPY --chown=app:app requirements/base.txt /edx/notes/requirements/base.txt
COPY --chown=app:app . /edx/notes
RUN pip install -r requirements/base.txt

USER app

CMD gunicorn --workers=2 --name notes --bind=0.0.0.0:8000 --log-file=/tmp/notes.log --max-requests=1000 notesserver.wsgi:application