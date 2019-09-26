edx-notes-api is a Django service used to store and serve notes taken by edX learners.  This folder 
contains Helm charts for deploying edx-notes-api on a `kubernetes`_ cluster with `helm`_

.. _kubernetes: http://kubernetes.io
.. _helm: https://helm.sh
.. _minikube: https://kubernetes.io/docs/tasks/tools/install-minikube

Prerequisites
------------

- Kubernetes 1.8+ cluster or `minikube`_ with PV support.
- kubectl configured
- helm configured

Installing Notes
------------

::

$ helm dependency build helmcharts/notes
$ helm package helmcharts/notes
$ helm install notes-x.y.z.tgz --name notes -f values.yaml


Uninstalling the Chart
------------

::

$ helm delete notes --purge

Upgrading an existing Release to a new major version
------------

::

$ helm dependency build helmcharts/notes
$ helm package helmcharts/notes
$ helm upgrade notes notes-x.y.z.tgz -f values.yaml

Notes-specific Configuration
------------

.. _mysql: https://github.com/helm/charts/tree/master/stable/mysql
.. _elasticsearch: https://github.com/elastic/helm-charts/tree/master/elasticsearch

edx notes has a `mysql`_ and `elasticsearch`_ subchart that can be toggled on or off depending on if you want to use external services or not.
See the links above for the chart parameters for those services.

https://github.com/helm/charts/tree/master/stable/mysql


===================================================================================================  ===================================================================================================  ===================================================================================================
Parameter                                                                                            Description                                                                                          Default                                                                                            
===================================================================================================  ===================================================================================================  ===================================================================================================
app.replicaCount                                                                                     Number of edx-notes-api-instances                                                                    1
app.image.repository                                                                                 Docker image repository to use for edx-notes-api                                                     edxops/notes
app.image.tag                                                                                        Docker image tag to use for edx-notes-api                                                            latest
app.image.pullPolicy                                                                                 Indicate if the edx-notes-api image should be pulled if you already                                  IfNotPresent
app.imagePullSecrets                                                                                 Image pull secrets for pulling the image from a private repo                                         []
app.nameOverride                                                                                     override the chart name                                                                                                 
app.fullnameOverride                                                                                 override the chart full name                                                                                                 
app.service.type                                                                                     k8s service type                                                                                     ClusterIP
app.service.port                                                                                     Notes k8s service port                                                                               8120
app.ingress.enabled                                                                                  If ingress is enabled for the notes service                                                          False
app.ingress.hosts                                                                                    Ingress hosts for the notes service                                                                  [{'host': 'notes.local', 'paths': []}]
app.ingress.tls                                                                                      Ingress tls config for notes                                                                         []
app.tolerations                                                                                      K8s tolerations for notes                                                                            []
app.extraInitContainers                                                                              Extra init containers for the notes pods                                                             []
app.config.ALLOWED_HOSTS                                                                             Hosts allowed to connect                                                                             ['*']
app.config.CLIENT_ID                                                                                 REQUIRED                                                                                                 
app.config.CLIENT_SECRET                                                                             REQUIRED                                                                                                 
app.config.DATABASES.default.ENGINE                                                                                                                                                                       django.db.backends.mysql
app.config.DATABASES.default.HOST                                                                                                                                                                         notes-mysql
app.config.DATABASES.default.NAME                                                                                                                                                                         notes-db
app.config.DATABASES.default.OPTIONS.connect_timeout                                                                                                                                                      10
app.config.DATABASES.default.PASSWORD                                                                REQUIRED                                                                                                 
app.config.DATABASES.default.PORT                                                                                                                                                                         3306
app.config.DATABASES.default.USER                                                                                                                                                                         notes-db-user
app.config.DISABLE_TOKEN_CHECK                                                                                                                                                                            False
app.config.ELASTICSEARCH_INDEX                                                                                                                                                                            edx_notes
app.config.ELASTICSEARCH_URL                                                                                                                                                                              http://notes-elasticsearch-master:9200
app.config.HAYSTACK_CONNECTIONS.default.ENGINE                                                                                                                                                            notesserver.highlight.ElasticsearchSearchEngine
app.config.HAYSTACK_CONNECTIONS.default.INDEX_NAME                                                                                                                                                        notes
app.config.HAYSTACK_CONNECTIONS.default.URL                                                                                                                                                               http://notes-elasticsearch-master:9200/
app.config.JWT_AUTH.JWT_AUTH_COOKIE_HEADER_PAYLOAD                                                                                                                                                        stage-edx-jwt-cookie-header-payload
app.config.JWT_AUTH.JWT_AUTH_COOKIE_SIGNATURE                                                                                                                                                             stage-edx-jwt-cookie-signature
app.config.JWT_AUTH.JWT_AUTH_REFRESH_COOKIE                                                                                                                                                               stage-edx-jwt-refresh-cookie
app.config.JWT_AUTH.JWT_ISSUERS                                                                                                                                                                           []
app.config.JWT_AUTH.JWT_PUBLIC_SIGNING_JWK_SET                                                                                                                                                            
app.config.RESULTS_DEFAULT_SIZE                                                                                                                                                                           25
app.config.RESULTS_MAX_SIZE                                                                                                                                                                               250
app.config.SECRET_KEY                                                                                REQUIRED                                                                                                 
app.config.USERNAME_REPLACEMENT_WORKER                                                                                                                                                                    username_replacement_service_worker
app.config.LOG_SETTINGS_LOG_DIR                                                                      logging directory                                                                                    /var/tmp
app.config.LOG_SETTINGS_LOGGING_ENV                                                                                                                                                                       no_env
app.config.LOG_SETTINGS_DEV_ENV                                                                                                                                                                           True
app.config.LOG_SETTINGS_DEBUG                                                                                                                                                                             True
app.config.LOG_SETTINGS_LOCAL_LOGLEVEL                                                                                                                                                                    INFO
app.config.LOG_SETTINGS_EDX_FILENAME                                                                                                                                                                      edx.log
app.config.LOG_SETTINGS_SERVICE_VARIANT                                                              logging service prefix                                                                               edx-notes-api
elasticsearch.enabled                                                                                set this to enabled if you want to enable the elasticsearch sub chart                                True
mysql.enabled                                                                                        set this to enabled if you want to enable the mysql sub chart                                        True
migrations.enabled                                                                                   set this to enabled to run migrations in an init container for each notes pod                        True
migrations.migrationContainerName                                                                    name of the migration container only used if migrations are enabled                                  notes-migrations
===================================================================================================  ===================================================================================================  ===================================================================================================


