#!/bin/bash

# Runs Elasticsearch
#
# Requires ESVER environment variable to be set.
# cwd is the git repository root.

set -e

if [[ $ESVER == "-" ]];
then
    exit 0
fi

echo "Starting ElasticSearch $ESVER" >&2
pushd elasticsearch-$ESVER
    # Elasticsearch 0.90 daemonizes automatically, but 1.0+ requires
    # a -d argument.

    if [[ $ESVER == 0* ]];
    then
        ./bin/elasticsearch
    else
        echo "launching with -d option." >&2
        ./bin/elasticsearch -d
        pip install elasticsearch==1.3.0
    fi
popd
