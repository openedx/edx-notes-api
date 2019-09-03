# Notes

[Notes](http://edx.org/todo) is a Django service used to store and serve notes taken by edX learners.

## TL;DR

```bash
# Testing configuration
$ eval $(minikube docker-env)
$ docker build . -t edxops/notes:latest
$ helm dependency build helmcharts/notes
$ helm package helmcharts/notes --destination helmcharts/notes
```

```bash
$ helm install helmcharts/notes/notes-0.1.0.tgz --name notes -f helmcharts/notes/values.yaml
```

## Introduction

This chart bootstraps a [Notes](https://edx.org/todo) deployment on a [Kubernetes](http://kubernetes.io) cluster using the [Helm](https://helm.sh) package manager.

This chart has been tested to work with NGINX Ingress, cert-manager, fluentd and Prometheus on top of the [BKPR](https://kubeprod.io/).

## Prerequisites

- Kubernetes 1.8+
- PV provisioner support in the underlying infrastructure

## Local Development:

See https://kubernetes.io/docs/tasks/tools/install-minikube for more information.  We are currently using the nginx minikube addon and the kubernetes dashbaord helmchart.

### TL;DR for Mac

```bash
brew cask install minikube
```

### TL;DR for Ubuntu
```bash
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 \
  && chmod +x minikube
sudo install minikube /usr/local/bin
```

### Run Nginx & Dashboard
```bash
minikube enable nginx
cat <<'EOF' >> dashboard.yml
---
enableSkipLogin: true
enableInsecureLogin: true
rbac:
  clusterAdminRole: true
ingress:
  enabled: true
  hosts:
    - k8s.dashboard
extraArgs:
  - --port=8443 # By default, https uses 8443 so we move it away to something else
  - --insecure-port=9090 # The chart has 8443 hard coded as a containerPort in the deployment spec so we must use this internally for the http service
  - --insecure-bind-address=0.0.0.0
service:
  type: ClusterIP
  # Not required, but less confusing
  externalPort: 8444
EOF
helm install stable/kubernetes-dashboard --name kubernetes-dashboard -f dashboard.yml
```

## Installing the Chart

To install the chart with the release name `notes`:

```bash
$ helm install helmcharts/notes/notes-0.1.0.tgz --name notes -f helmcharts/notes/values.yaml
```

The command deploys Notes on the Kubernetes cluster in the default configuration. The [configuration](#configuration) section lists the parameters that can be configured during installation.

> **Tip**: List all releases using `helm list`

## Uninstalling the Chart

To uninstall/delete the `notes` deployment:

```bash
$ helm delete notes --purge
```

The command removes all the Kubernetes components associated with the chart and deletes the release.

## Upgrading an existing Release to a new major version

A major chart version change (like v1.2.3 -> v2.0.0) indicates that there is an
incompatible breaking change needing manual actions.

### To 1.0.0

<todo>

## Configuration

The following table lists the configurable parameters of the Notes chart and their default values.

| Parameter                                     | Description                                                                                                                                         | Default                                                 |
|-----------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------|
| `global.imageRegistry`                        | Global Docker image registry                                                                                                                        | `nil`                                                   |
| `sysctlImage.resources`                       | sysctlImage Init container CPU/Memory resource requests/limits                                                                                      | {}                                                      |

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`. For example,

```bash
$ helm install --name notes \
  --set token=secretpassword \
  --name notes -f helmcharts/notes/values.yaml
```

The above command sets the token to `secrettoken`.

Alternatively, a YAML file that specifies the values for the parameters can be provided while installing the chart. For example,

```bash
$ helm install --name notes -f values.yaml <todo>
```

> **Tip**: You can use the default [values.yaml](values.yaml)

> **Note for minikube users**: Current versions of minikube (v0.24.1 at the time of writing) provision `hostPath` persistent volumes that are only writable by root. Using chart defaults cause pod failure for the Redis pod as it attempts to write to the `/bitnami` directory. Consider installing Redis with `--set persistence.enabled=false`. See minikube issue [1990](https://github.com/kubernetes/minikube/issues/1990) for more information.

### Using password file
To use a token file for Notes you need to create a secret containing the password:

```bash
$ kubectl create secret generic rnotes-token-file --from-file=/tmp/notes-token
```
> *NOTE*: It is important that the file with the password must be called `notes-token`

And deploy the Helm Chart using the secret name:

```bash
$ helm install notes --set usePassword=true,useTokenFile=true,existingSecret=notes-token-file,sentinels.enabled=true,metrics.enabled=true
```

### Production configuration

This chart will include a `values-production.yaml` file where you can find some parameters oriented to production configuration in comparison to the regular `values.yaml`.

```console
$ helm install --name notes -f ./values-production.yaml
```

- Number of slaves:
```diff
- cluster.slaveCount: 2
+ cluster.slaveCount: 3
```

- Enable NetworkPolicy:
```diff
- networkPolicy.enabled: false
+ networkPolicy.enabled: true
```

- Start a side-car prometheus exporter:
```diff
- metrics.enabled: false
+ metrics.enabled: true
```

### [Rolling VS Immutable tags](https://docs.bitnami.com/containers/how-to/understand-rolling-tags-containers/)

It is strongly recommended to use immutable tags in a production environment. This ensures your deployment does not change automatically if the same tag is updated with a different image.

Bitnami will release a new chart updating its containers if a new version of the main container, significant changes, or critical vulnerabilities exist.

## NetworkPolicy

To enable network policy for Notes, install
[a networking plugin that implements the Kubernetes NetworkPolicy spec](https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy#before-you-begin),
and set `networkPolicy.enabled` to `true`.

For Kubernetes v1.5 & v1.6, you must also turn on NetworkPolicy by setting
the DefaultDeny namespace annotation. Note: this will enforce policy for _all_ pods in the namespace:

    kubectl annotate namespace default "net.beta.kubernetes.io/network-policy={\"ingress\":{\"isolation\":\"DefaultDeny\"}}"

With NetworkPolicy enabled, only pods with the generated client label will be
able to connect to Notes. This label will be displayed in the output
after a successful install.

## Metrics

The chart optionally can start a metrics exporter for [prometheus](https://prometheus.io). The metrics endpoint (port 9121) is exposed in the service. Metrics can be scraped from within the cluster using something similar as the described in the [example Prometheus scrape configuration](https://github.com/prometheus/prometheus/blob/master/documentation/examples/prometheus-kubernetes.yml). If metrics are to be scraped from outside the cluster, the Kubernetes API proxy can be utilized to access the endpoint.

## Notable changes

### 1.0.0
<todo>