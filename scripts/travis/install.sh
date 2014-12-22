#!/bin/bash

# Installs Elasticsearch
#
# Requires ESVER environment variable to be set.

set -e

if [[ $ESVER == "-" ]];
then
    exit 0
fi

echo "Installing ElasticSearch $ESVER" >&2
wget https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-$ESVER.tar.gz
tar xzvf elasticsearch-$ESVER.tar.gz
