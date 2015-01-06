Part of `edX code`__.

__ http://code.edx.org/

edX Student Notes API |build-status| |coverage-status|
======================================================

This is a backend store for edX Student Notes.

Overview
--------

The edX Notes API is designed to be compatible with the
`Annotator <http://annotatorjs.org/>`__.

Getting Started
---------------

1. You'll need an `ElasticSearch <http://elasticsearch.org>`__ installed.

2. Install the requirements:

   ::

       $ make develop

3. Create index and put mapping:

   ::

       $ make create-index

4. Run the server:

   ::

       $ make run

Running Tests
-------------

Run ``make validate`` install the requirements, run the tests, and run
lint.

License
-------

The code in this repository is licensed under version 3 of the AGPL unless
otherwise noted.

Please see ``LICENSE.txt`` for details.

How To Contribute
-----------------

Contributions are very welcome.

Please read `How To Contribute <https://github.com/edx/edx-platform/blob/master/CONTRIBUTING.rst>`_ for details.

Even though it was written with ``edx-platform`` in mind, the guidelines
should be followed for Open edX code in general.

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org

Mailing List and IRC Channel
----------------------------

You can discuss this code on the `edx-code Google Group`__ or in the
``edx-code`` IRC channel on Freenode.

__ https://groups.google.com/forum/#!forum/edx-code

.. |build-status| image:: https://travis-ci.org/edx/edx-notes-api.svg?branch=master
   :target: https://travis-ci.org/edx/edx-notes-api
.. |coverage-status| image:: https://coveralls.io/repos/edx/edx-notes-api/badge.png?branch=master
   :target: https://coveralls.io/r/edx/edx-notes-api?branch=master
