# Notes Helm Chart

[Notes](http://edx.org) is a Django service used to store and serve notes taken by edX learners.  This folder 
contains Helm charts for deploying Notes on a [Kubernetes](http://kubernetes.io) cluster with [Helm](https://helm.sh).

The Notes chart has been tested to work with NGINX Ingress, cert-manager, fluentd and Prometheus.

This package is a part of the edX Infrastructure as Code Library, a collection of reusable, production ready 
infrastructure code. Read the DevOps Philosophy document to learn more about how Gruntwork builds production 
grade infrastructure code.

## Prerequisites

- Kubernetes 1.8+ or [minikube](https://kubernetes.io/docs/tasks/tools/install-minikube) with an ingress controller and the [kubernetes dashboard](https://github.com/helm/charts/tree/master/stable/kubernetes-dashboard).
- PV provisioner support in the underlying infrastructure

### For Mac

```bash
brew cask install minikube
minikube start --vm-driver hyperkit --bootstrapper kubeadm --memory=10000 --cpus=6
```

### For Ubuntu
```bash
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 \
  && chmod +x minikube
sudo install minikube /usr/local/bin
minikube start --memory=10000 --cpus=6
```

### Nginx Ingress Conroller & Kubernetes Dashboard
```bash
eval $(minikube docker-env) # You may want this in your .bashrc or .zshrc
kubectl -n kube-system create serviceaccount tiller
minikube addons enable ingress
kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller
helm init --service-account=tiller
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
sudo -- sh -c -e "echo '$(minikube ip)     k8s.dashboard' >> /etc/hosts";
```

## What is Kubernetes?

[Kubernetes](https://kubernetes.io) is an open source container management system for deploying, scaling, and managing
containerized applications. Kubernetes is built by Google based on their internal proprietary container management
systems (Borg and Omega). Kubernetes provides a cloud agnostic platform to deploy your containerized applications with
built in support for common operational tasks such as replication, autoscaling, self-healing, and rolling deployments.

You can learn more about Kubernetes from [the official documentation](https://kubernetes.io/docs/tutorials/kubernetes-basics/).


## What is Helm?

[Helm](https://helm.sh/) is a package and module manager for Kubernetes that allows you to define, install, and manage
Kubernetes applications as reusable packages called Charts. Helm provides support for official charts in their
repository that contains various applications such as Jenkins, MySQL, and Consul to name a few. Gruntwork uses Helm
under the hood for the Kubernetes modules in this package.

Helm consists of two components: the Helm Client, and the Helm Server (Tiller)

### What is the Helm Client?

The Helm client is a command line utility that provides a way to interact with Tiller. It is the primary interface to
installing and managing Charts as releases in the Helm ecosystem. In addition to providing operational interfaces (e.g
install, upgrade, list, etc), the client also provides utilities to support local development of Charts in the form of a
scaffolding command and repository management (e.g uploading a Chart).

### What is the Helm Server?

The Helm Server (Tiller) is a component of Helm that runs inside the Kubernetes cluster. Tiller is what
provides the functionality to apply the Kubernetes resource descriptions to the Kubernetes cluster. When you install a
release, the helm client essentially packages up the values and charts as a release, which is submitted to Tiller.
Tiller will then generate Kubernetes YAML files from the packaged release, and then apply the generated Kubernetes YAML
file from the charts on the cluster.


## How do you run applications on Kubernetes?

There are three different ways you can schedule your application on a Kubernetes cluster. In all three, your application
Docker containers are packaged as a [Pod](https://kubernetes.io/docs/concepts/workloads/pods/pod/), which are the
smallest deployable unit in Kubernetes, and represent one or more Docker containers that are tightly coupled. Containers
in a Pod share certain elements of the kernel space that are traditionally isolated between containers, such as the
network space (the containers both share an IP and thus the available ports are shared), IPC namespace, and PIDs in some
cases.

Pods are considered to be relatively ephemeral disposable entities in the Kubernetes ecosystem. This is because Pods are
designed to be mobile across the cluster so that you can design a scalable fault tolerant system. As such, Pods are
generally scheduled with
[Controllers](https://kubernetes.io/docs/concepts/workloads/pods/pod-overview/#pods-and-controllers) that manage the
lifecycle of a Pod. Using Controllers, you can schedule your Pods as:

- Jobs, which are Pods with a controller that will guarantee the Pods run to completion. See the [k8s-job
  chart](/charts/k8s-job) for more information.
- Deployments behind a Service, which are Pods with a controller that implement lifecycle rules to provide replication
  and self-healing capabilities. Deployments will automatically reprovision failed Pods, or migrate Pods to healthy
  nodes off of failed nodes. A Service constructs a consistent endpoint that can be used to access the Deployment. See
  the [k8s-service chart](/charts/k8s-service) for more information.
- Daemon Sets, which are Pods that are scheduled on all worker nodes. Daemon Sets schedule exactly one instance of a Pod
  on each node. Like Deployments, Daemon Sets will reprovision failed Pods and schedule new ones automatically on
  new nodes that join the cluster. See the [k8s-daemon-set chart](/charts/k8s-daemon-set) for more information.

<!-- TODO: ## What parts of the Production Grade Infrastructure Checklist are covered by this Module? -->

## Installing Notes

To install the chart with the release name `notes`:

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

The command deploys Notes on the Kubernetes cluster in the default configuration. The [configuration](#configuration) section lists the parameters that can be configured during installation.

> **Tip**: List all releases using `helm list`

## Uninstalling the Chart

To uninstall/delete the `notes` deployment:

```bash
$ helm delete notes --purge
```

## Deleting Minikube

```bash
$ minikube delete
```

The command removes all the Kubernetes components associated with the chart and deletes the release.

## Upgrading an existing Release to a new major version

A major chart version change (like v1.2.3 -> v2.0.0) indicates that there is an
incompatible breaking change needing manual actions.

<!-- TODO: ## 
### To 1.0.0

How do we perform these upgrades

-->

## Configuration

The following table lists the configurable parameters of the Notes chart and their default values.

| Parameter                                     | Description                                                                                                                                         | Default                                                 |
|-----------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------|
| `global.imageRegistry`                        | Global Docker image registry                                                                                                                        | `nil`                                                   |
| `sysctlImage.resources`                       | sysctlImage Init container CPU/Memory resource requests/limits                                                                                      | {}                                                      |

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`. For example,

```bash
$ helm install helmcharts/notes/notes-0.1.0.tgz \
  --name notes \
  --set token=secrettoken \
  --name notes
```

The above command sets the token to `secrettoken`.

Alternatively, a YAML file that specifies the values for the parameters can be provided while installing the chart. For example,

```bash
$ helm install helmcharts/notes/notes-0.1.0.tgz \
  --name notes \
  -f helmcharts/notes/values.yaml
```

> **Tip**: You can use the default [values.yaml](values.yaml)

> **Note for minikube users**: Current versions of minikube (v0.24.1 at the time of writing) provision `hostPath` persistent volumes that are only writable by root.

### Using token file
To use a token file for Notes you need to create a secret containing the password:

```bash
$ kubectl create secret generic rnotes-token-file --from-file=/tmp/notes-token
```
> *NOTE*: It is important that the file with the password must be called `notes-token`

And deploy the Helm Chart using the secret name:

```bash
$ helm install notes --set useTokenFile=true,existingSecret=notes-token-file,sentinels.enabled=true,metrics.enabled=true
```

<!-- TODO: ## Not yet implemented
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
-->

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
First version of the helmchart depending on the stable mysql and elasticsearch charts and using an init container for running migrations.