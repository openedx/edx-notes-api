edX Student Notes API |build-status|
####################################

This is a backend store for edX Student Notes.

Overview
********

The edX Notes API is designed to be compatible with the `Annotator <http://annotatorjs.org/>`__.

Getting Started
***************

1. Install `ElasticSearch 7.13.4 <https://www.elastic.co/downloads/past-releases/elasticsearch-7-13-4>`__.

2. Install the requirements:

   .. code-block:: bash

      make develop

3. Create index and put mapping:

   .. code-block:: bash

      make create-index

4. Run the server:

   .. code-block:: bash

      make run

Configuration
*************

``CLIENT_ID`` - OAuth2 Client ID, which is to be found in ``aud`` field of IDTokens which authorize users

``CLIENT_SECRET`` - secret with which IDTokens should be encoded

``ES_DISABLED`` - set to True when you need to run the service without ElasticSearch support.
                  e.g if it became corrupted and you're rebuilding the index, while still serving users
                  through MySQL

``ELASTICSEARCH_DSL['default']['hosts']`` - Your ElasticSearch host

Running Tests
*************

Install requirements::

   make test.requirements

Start mysql/elasticsearch services::

   make test-start-services

Run unit tests::

   make test

Run quality checks::

   make quality

How To Resync The Index
***********************

edX Notes Store uses `Django elasticsearch DSL <https://django-elasticsearch-dsl.readthedocs.io/>`_ which comes with several management commands.

Please read more about ``search_index`` management commands
`here <https://django-elasticsearch-dsl.readthedocs.io/en/latest/management.html>`_.

License
*******

The code in this repository is licensed under version 3 of the AGPL unless
otherwise noted.

Please see ``LICENSE.txt`` for details.

How To Contribute
*****************

Contributions are very welcome.

Please read `How To Contribute <https://openedx.atlassian.net/wiki/spaces/COMM/pages/941457737/How+to+Start+Contributing+Code>`_ for details.

Reporting Security Issues
*************************

Please do not report security issues in public. Please email security@openedx.org

Mailing List and IRC Channel
****************************

You can discuss this code on the `edx-code Google Group`__ or in the
``edx-code`` IRC channel on Freenode.

__ https://groups.google.com/g/edx-code

.. |build-status| image:: https://github.com/openedx/edx-notes-api/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/openedx/edx-notes-api/actions/workflows/ci.yml

