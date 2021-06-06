terraform {
  required_version = ">= 0.13"
  required_providers {
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = ">= 1.7.0"
    }
  }
}


##################
# Set up connection to GKE
##################
data "google_client_config" "default" {
}

provider "kubernetes" {
  host                   = var.cluster_endpoint
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(var.cluster_ca_cert)
}
provider "helm" {
  kubernetes {
    host                   = var.cluster_endpoint
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(var.cluster_ca_cert)
  }
}
provider "kubectl" {
  host                   = var.cluster_endpoint
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(var.cluster_ca_cert)
}



data "template_file" "kubeconfig" {
  template = file("${path.module}/kubeconfig.yml")

  vars = {
    cluster_name  = var.cluster_name
    endpoint      = var.cluster_endpoint
    cluster_ca    = var.cluster_ca_cert
    cluster_token = data.google_client_config.default.access_token
  }
}
# I believe this is needed to persist auth for more than 60 minutes
# careful!  this is sensitive, I believe
resource "local_file" "kubeconfig" {
  depends_on = [var.cluster_id]
  content    = data.template_file.kubeconfig.rendered
  filename   = "${path.root}/kubeconfig"
}

##################
# Create Kubernetes resources
##################
resource "kubernetes_namespace" "sparkplane" {
  metadata {
    name = "${var.namespace}-${var.organization}"
  }
  depends_on = [local_file.kubeconfig]
}

resource "kubernetes_namespace" "serviceplane" {
  metadata {
    name = "serviceplane-${var.organization}"
  }
  depends_on = [local_file.kubeconfig]
}

/*
resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
  }
  depends_on = [local_file.kubeconfig]
}
*/

##################
# Map GCP service accounts to kubernetes service accounts
##################


# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# this works with google service account binding to connect kubernetes and google accounts
resource "kubernetes_service_account" "docker-cfg-write-events" {
  metadata {
    name      = "docker-cfg-write"
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
    annotations = {
      "iam.gke.io/gcp-service-account" = var.docker_write_svc_email
    }
  }
  depends_on = [kubernetes_namespace.serviceplane]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "bind_docker_write_argo" {
  service_account_id = var.docker_write_svc_name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${kubernetes_namespace.serviceplane.metadata.0.name}/${kubernetes_service_account.docker-cfg-write-events.metadata.0.name}]",
  ]
  depends_on = [
    kubernetes_service_account.docker-cfg-write-events
  ]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# this works with google service account binding to connect kubernetes and google accounts
resource "kubernetes_service_account" "spark-history" {
  metadata {
    name      = "spark-history"
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
    annotations = {
      "iam.gke.io/gcp-service-account" = var.spark_history_svc_email
    }
  }
  depends_on = [kubernetes_namespace.serviceplane]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "spark-history" {
  service_account_id = var.spark_history_svc_name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${kubernetes_namespace.serviceplane.metadata.0.name}/${kubernetes_service_account.spark-history.metadata.0.name}]",
  ]
  depends_on = [
    kubernetes_service_account.spark-history
  ]
}


# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# this works with google service account binding to connect kubernetes and google accounts
resource "kubernetes_service_account" "firestore" {
  metadata {
    name      = "firestore"
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
    annotations = {
      "iam.gke.io/gcp-service-account" = var.firestore_svc_email
    }
  }
  depends_on = [kubernetes_namespace.serviceplane]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "firestore" {
  service_account_id = var.firestore_svc_name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${kubernetes_namespace.serviceplane.metadata.0.name}/${kubernetes_service_account.firestore.metadata.0.name}]",
  ]
  depends_on = [
    kubernetes_namespace.serviceplane
  ]
}


# use this for running steps in argo
resource "kubernetes_role" "argorules" {
  metadata {
    name      = "argoroles"
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
  }
  rule {
    api_groups = [""]
    resources  = ["pods"]
    verbs      = ["get", "list", "watch", "patch"]
  }
  rule {
    api_groups = ["argoproj.io"]
    resources  = ["workflows"]
    verbs      = ["get", "list"]
  }
  depends_on = [kubernetes_namespace.serviceplane]
}

resource "kubernetes_role_binding" "dockerwrite" {
  metadata {
    name      = "dockerwriteargopermissions-role-binding"
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.argorules.metadata.0.name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.docker-cfg-write-events.metadata.0.name
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
  }
}

resource "kubernetes_role_binding" "firestore" {
  metadata {
    name      = "firestorepermissions-role-binding"
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.argorules.metadata.0.name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.firestore.metadata.0.name
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
  }
}


# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# this works with google service account binding to connect kubernetes and google accounts
resource "kubernetes_service_account" "spark" {
  metadata {
    name      = "spark"
    namespace = kubernetes_namespace.sparkplane.metadata.0.name
    annotations = {
      "iam.gke.io/gcp-service-account" = var.spark_gcs_svc_email
    }
  }
  depends_on = [kubernetes_namespace.sparkplane]
}


# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "spark" {
  service_account_id = var.spark_gcs_svc_name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${kubernetes_namespace.sparkplane.metadata.0.name}/${kubernetes_service_account.spark.metadata.0.name}]",
  ]
  depends_on = [
    kubernetes_namespace.sparkplane
  ]
}



## needed for operating spark resources
resource "kubernetes_role" "sparkrules" {
  metadata {
    name      = "sparkrules"
    namespace = kubernetes_namespace.sparkplane.metadata.0.name
  }
  rule {
    api_groups = [""]
    resources  = ["pods", "configmaps"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }
  depends_on = [kubernetes_namespace.sparkplane]
}

resource "kubernetes_role_binding" "sparkrules" {
  metadata {
    name      = "sparkrules-role-binding"
    namespace = kubernetes_namespace.sparkplane.metadata.0.name
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.sparkrules.metadata.0.name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.spark.metadata.0.name
    namespace = kubernetes_namespace.sparkplane.metadata.0.name
  }
  depends_on = [kubernetes_namespace.sparkplane]
}


# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# this works with google service account binding to connect kubernetes and google accounts
resource "kubernetes_service_account" "argo" {
  metadata {
    name      = "argo-workflow"
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
    annotations = {
      "iam.gke.io/gcp-service-account" = var.argo_svc_email
    }
  }
  depends_on = [kubernetes_namespace.serviceplane]
}


# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "argo" {
  service_account_id = var.argo_svc_name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "serviceAccount:${var.project}.svc.id.goog[${kubernetes_namespace.serviceplane.metadata.0.name}/${kubernetes_service_account.argo.metadata.0.name}]",
  ]
  depends_on = [
    kubernetes_namespace.serviceplane
  ]
}



# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# this works with google service account binding to connect kubernetes and google accounts
resource "kubernetes_service_account" "firestoreviewer" {
  metadata {
    name      = "firestore-viewer"
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
    annotations = {
      "iam.gke.io/gcp-service-account" = var.firestoreviewer_svc_email
    }
  }
  depends_on = [kubernetes_namespace.serviceplane]
}


# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "firestoreviewer" {
  service_account_id = var.firestoreviewer_svc_name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "serviceAccount:${var.project}.svc.id.goog[${kubernetes_namespace.serviceplane.metadata.0.name}/${kubernetes_service_account.firestoreviewer.metadata.0.name}]",
  ]
  depends_on = [
    kubernetes_namespace.serviceplane
  ]
}


##################
# Standalone kubernetes service accounts and secrets
##################

# this will have worklow permissions 


resource "kubernetes_role_binding" "argoevents-runrb" {
  metadata {
    name      = "argoevents-runsa-role-binding"
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.argorules.metadata.0.name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.argo.metadata.0.name
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
  }
  depends_on = [kubernetes_namespace.serviceplane]
}

# todo, define this once for whole cluster
resource "kubernetes_cluster_role" "stopsparkapplication" {
  metadata {
    name = "stopsparkapp-role"
  }
  rule {
    api_groups = ["sparkoperator.k8s.io"]
    resources  = ["sparkapplications"]
    verbs      = ["delete"]
  }
  depends_on = [kubernetes_namespace.serviceplane]
}

# This is per organization
resource "kubernetes_role_binding" "stopsparkapplication" {
  metadata {
    name      = "stopspark-role-binding"
    namespace = kubernetes_namespace.sparkplane.metadata.0.name
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.stopsparkapplication.metadata.0.name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.firestoreviewer.metadata.0.name
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
  }
  depends_on = [kubernetes_namespace.serviceplane]
}


# Todo, define this once for the whole cluster
resource "kubernetes_cluster_role" "launchsparkapplication" {
  metadata {
    name = "launchsparkapplication-role"
  }
  rule {
    api_groups = ["sparkoperator.k8s.io"]
    resources  = ["sparkapplications"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }
  rule {
    api_groups = [""]
    resources  = ["services"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }
  rule {
    api_groups = ["batch"]
    resources  = ["jobs"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }
  depends_on = [kubernetes_namespace.serviceplane]
}

# This is per organization
resource "kubernetes_role_binding" "launchsparkapplication" {
  metadata {
    name      = "launchspark-role-binding"
    namespace = kubernetes_namespace.sparkplane.metadata.0.name
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.launchsparkapplication.metadata.0.name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.argo.metadata.0.name
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
  }
  depends_on = [kubernetes_namespace.serviceplane]
}



#### Data
# do I need these?  or could I justpass them declaratively as 
# needed?
resource "kubernetes_config_map" "usefuldata" {
  metadata {
    name      = "sparkjobdata"
    namespace = kubernetes_namespace.sparkplane.metadata.0.name
  }

  data = {
    port         = "9042"
    organization = var.organization # may not need this, could pass this in
    project      = var.project
    org_bucket   = var.spark_storage_bucket_url
    # add checkpoint location here...
    spark_namespace = kubernetes_namespace.sparkplane.metadata.0.name
  }

  depends_on = [kubernetes_namespace.sparkplane]
}
resource "kubernetes_config_map" "usefuldataargo" {
  metadata {
    name      = "sparkjobdata"
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
  }

  data = {
    port         = "9042"
    organization = var.organization
    project      = var.project
    org_bucket   = var.spark_storage_bucket_url
    # add checkpoint location here...
    spark_namespace = kubernetes_namespace.sparkplane.metadata.0.name
  }

  depends_on = [kubernetes_namespace.serviceplane, kubernetes_namespace.sparkplane]
}


##################
# Install Spark
##################
##########
# Todo, this should be one per cluster
# We will be multi-tenant so this should be in its own environment
# Move this to the "global" section of kuberentes
##########
resource "helm_release" "spark" {
  name             = "spark-operator"
  namespace        = "spark-operator"
  create_namespace = true
  repository       = "https://googlecloudplatform.github.io/spark-on-k8s-operator"
  chart            = "spark-operator"
  set {
    name  = "webhook.enable"
    value = true
  }
  set {
    name  = "metrics.enable"
    value = false //local prometheus shouldn't scrape global operator
  }
  depends_on = [local_file.kubeconfig]
}

##################
# Install Spark History
##################
resource "helm_release" "sparkhistory" { # todo, override "loadbalancer" 
  name      = "spark-history-server"
  namespace = kubernetes_namespace.serviceplane.metadata.0.name
  #create_namespace = true
  repository = "https://charts.helm.sh/stable"
  chart      = "spark-history-server"
  values = [
    "${templatefile("../../monitoring/sparkhistory.yml", {
      project                    = var.project
      sparkhistoryserviceaccount = kubernetes_service_account.spark-history.metadata.0.name
      sparkhistorybucketurl      = var.spark_storage_bucket_url
      sparkhistoryname           = "spark-history-server/"
      organization               = var.organization
    })}"
  ]

  # set {
  #   name  = "serviceAccount.create"
  #   value = "false"
  # }
  # set {
  #   name  = "serviceAccount.name"
  #   value = kubernetes_service_account.spark-history.metadata.0.name
  # }
  # set {
  #   name  = "gcs.logDirectory"
  #   value = var.spark_history_bucket_url
  # }
  # set {
  #   name  = "gcs.enableGCS" # I added permission to the spark history bucket to the kubernetes cluster service account
  #   value = "true"
  # }
  # set {
  #   name  = "gcs.enableIAM"
  #   value = "true"
  # }
  # set {
  #   name  = "pvc.enablePVC"
  #   value = "false"
  # }
  # set {
  #   name  = "nfs.enableExampleNFS"
  #   value = "false"
  # }
  # set {
  #   name  = "image.repository"
  #   value = "us-central1-docker.pkg.dev/${var.project}/${var.project}/sparkhistory"
  # }
  # set {
  #   name  = "image.tag"
  #   value = "v0.2.0"
  # }
  # set {
  #   name  = "image.pullPolicy"
  #   value = "IfNotPresent"
  # }
  # set {
  #   name  = "service.type"
  #   value = "NodePort"
  # }
  # set {
  #   name  = "environment.SPARK_PUBLIC_DNS"
  #   value = "https://${var.organization}.streamstate.org/sparkhistory/"
  # }
  depends_on = [kubernetes_service_account.spark-history]
}

##################
# Install Password Generator
##################
resource "helm_release" "passwordgenerator" {
  name      = "kubernetes-secret-generator"
  namespace = kubernetes_namespace.serviceplane.metadata.0.name //"passwordgenerate-${var.organization}"
  //create_namespace = true
  repository = "https://helm.mittwald.de"
  chart      = "kubernetes-secret-generator"
  set {
    name  = "secretLength"
    value = 32
  }
  set {
    name  = "watchNamespace"
    value = kubernetes_namespace.serviceplane.metadata.0.name
  }
  depends_on = [kubernetes_namespace.serviceplane]
}

data "kubectl_file_documents" "oidcsecret" {
  content = templatefile("../../gateway/oidc.yml", {
    client_id     = base64encode(var.client_id),
    client_secret = base64encode(var.client_secret)
  })
}
resource "kubectl_manifest" "oidcsecret" {
  count              = 1
  yaml_body          = element(data.kubectl_file_documents.oidcsecret.documents, count.index)
  override_namespace = kubernetes_namespace.serviceplane.metadata.0.name
  depends_on         = [helm_release.passwordgenerator]
}


data "kubectl_file_documents" "token" {
  content = file("../../gateway/token.yml")
}
resource "kubectl_manifest" "token" {
  count              = length(data.kubectl_file_documents.token.documents)
  yaml_body          = element(data.kubectl_file_documents.token.documents, count.index)
  override_namespace = kubernetes_namespace.serviceplane.metadata.0.name
  depends_on         = [helm_release.passwordgenerator]
}


##################
# Install Nginx
##################
# Todo, this should be installed cluster wide
resource "helm_release" "nginx" {
  name             = "nginx-ingress"
  namespace        = "nginx"
  create_namespace = true
  #repository       = "https://helm.nginx.com/stable"
  repository = "https://kubernetes.github.io/ingress-nginx"
  #chart      = "nginx-ingress"
  chart = "ingress-nginx"

  values = [
    "${templatefile("../../gateway/nginx.yml", {
      static_ip_address = var.staticip_address
    })}"
  ]
}




##################
# install cert manager
##################
# shoudl this be installed once per cluster?
## I believe so, yes.  Then each organization
# gets their own Issuer

locals {
  dns_service_account = "cert-manager"
}
resource "helm_release" "certmanager" {
  name      = "cert-manager"
  namespace = kubernetes_namespace.serviceplane.metadata.0.name

  repository = "https://charts.jetstack.io"
  chart      = "cert-manager"
  values = [
    "${templatefile("../../gateway/certmanager.yml", {
      serviceaccountname     = local.dns_service_account
      gcpserviceaccountemail = var.dns_svc_email
    })}"
  ]
  ## TODO is this even needed anymore? yes, if using dns in cert issuer
}
resource "google_service_account_iam_binding" "dns" {
  service_account_id = var.dns_svc_name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${kubernetes_namespace.serviceplane.metadata.0.name}/${local.dns_service_account}]",
  ]
  depends_on = [
    helm_release.certmanager //helm creates the service account for me
  ]
}

data "kubectl_path_documents" "certs" {
  pattern = "../../gateway/certs.yml"
  vars = {
    organization = var.organization
    project      = var.project
  }
}
resource "kubectl_manifest" "certs" {
  count              = length(data.kubectl_path_documents.certs.documents) # 17
  yaml_body          = element(data.kubectl_path_documents.certs.documents, count.index)
  override_namespace = kubernetes_namespace.serviceplane.metadata.0.name
  depends_on = [
    kubernetes_namespace.serviceplane,
    helm_release.certmanager
  ]
}



##################
# Install Prometheus
##################

## waiting on https://github.com/prometheus-community/helm-charts/issues/969
resource "helm_release" "prometheus" {
  name       = "prometheus"
  namespace  = kubernetes_namespace.serviceplane.metadata.0.name
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack" # includes prometheus operator
  values = [
    "${templatefile("../../monitoring/prometheus_helm_values.yml", {
      organization          = var.organization
      serviceplane          = kubernetes_namespace.serviceplane.metadata.0.name
      sparkplane            = kubernetes_namespace.sparkplane.metadata.0.name
      prometheusclusterrole = "notused" # kubernetes_cluster_role.prometheusclusterrole.metadata.0.name
    })}"
  ]
  depends_on = [
    kubernetes_namespace.serviceplane,
    kubernetes_namespace.sparkplane,
    # kubectl_manifest.prometheusclusterrole
  ]
}

# still having issues with preinstalled charts, see https://github.com/grafana/helm-charts/issues/200#issuecomment-775572514
resource "helm_release" "grafana" {
  name       = "grafana"
  namespace  = kubernetes_namespace.serviceplane.metadata.0.name
  repository = "https://grafana.github.io/helm-charts"
  chart      = "grafana"
  # version    = "6.9.1"
  values = [
    "${templatefile("../../monitoring/grafana_helm_values.yml", {
      organization  = var.organization
      DS_PROMETHEUS = "Prometheus"
    })}"
  ]
  depends_on = [
    kubernetes_namespace.serviceplane,
  ]
}

###################
# Install servicemonitor for spark
###################

/*
data "kubectl_file_documents" "sparkoperatorprometheus" {
  content = templatefile("../../kubernetes_resources/prometheus_spark.yml", {
    operatornamespace   = helm_release.spark.metadata.0.namespace
    monitoringnamespace = kubernetes_namespace.monitoring.metadata.0.name
  })
}
resource "kubectl_manifest" "sparkoperatorprometheus" {
  count      = 2
  yaml_body  = element(data.kubectl_file_documents.sparkoperatorprometheus.documents, count.index)
  depends_on = [kubectl_manifest.prometheusinstall, helm_release.spark]
}*/



##################
# Install Argo
##################

resource "helm_release" "argoworkflow" {
  name       = "argoworkflow"
  namespace  = kubernetes_namespace.serviceplane.metadata.0.name
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-workflows"
  values = [
    "${templatefile("../../argo/argoworkflow_helm_values.yml", {
      organization   = var.organization
      serviceaccount = kubernetes_service_account.argo.metadata.0.name # does this matter? or is it overwritten when using it in the pysparkworkflow.yml?
      namespace      = kubernetes_namespace.serviceplane.metadata.0.name
    })}"
  ]
  depends_on = [
    kubernetes_namespace.serviceplane, helm_release.prometheus
  ]
}


resource "helm_release" "argoevents" {
  name       = "argoevents"
  namespace  = kubernetes_namespace.serviceplane.metadata.0.name
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-events"
  values = [
    "${templatefile("../../argo/argoevents_helm_values.yml", {
      namespace = kubernetes_namespace.serviceplane.metadata.0.name
    })}"
  ]
  depends_on = [
    kubernetes_namespace.serviceplane,
    helm_release.argoworkflow
  ]
}


data "kubectl_file_documents" "argoeventswebhook" {
  content = file("../../argo/webhookinstall.yml")
}

resource "kubectl_manifest" "argoeventswebhook" {
  count              = length(data.kubectl_file_documents.argoeventswebhook.documents)
  yaml_body          = element(data.kubectl_file_documents.argoeventswebhook.documents, count.index)
  override_namespace = kubernetes_namespace.serviceplane.metadata.0.name
  depends_on         = [helm_release.argoevents]
}

data "kubectl_path_documents" "pysparkeventworkflow" {
  pattern = "../../argo/pysparkworkflow.yml"
  vars = {
    project           = var.project
    organization      = var.organization
    dockersecretwrite = kubernetes_service_account.docker-cfg-write-events.metadata.0.name
    registry          = var.org_registry
    registryprefix    = var.registryprefix
    runserviceaccount = kubernetes_service_account.argo.metadata.0.name
    # sparksubmitserviceaccount = kubernetes_service_account.argoevents-sparksubmit.metadata.0.name
    sparkserviceaccount     = kubernetes_service_account.spark.metadata.0.name
    firestoreserviceaccount = kubernetes_service_account.firestore.metadata.0.name
    dataconfig              = kubernetes_config_map.usefuldata.metadata.0.name
    dataconfigargo          = kubernetes_config_map.usefuldataargo.metadata.0.name
    namespace               = kubernetes_namespace.sparkplane.metadata.0.name
    monitoringnamespace     = kubernetes_namespace.serviceplane.metadata.0.name
    spark_history_name      = "spark-history-server/"
    #spark_history_bucket_url = var.spark_history_bucket_url
    spark_storage_bucket_url = var.spark_storage_bucket_url
    bucketwithoutgs          = replace(var.spark_storage_bucket_url, "gs://", "")
  }
}

resource "kubectl_manifest" "pysparkeventworkflow" {
  count              = 1 # length(data.kubectl_path_documents.pysparkeventworkflow.documents)
  yaml_body          = element(data.kubectl_path_documents.pysparkeventworkflow.documents, count.index)
  override_namespace = kubernetes_namespace.serviceplane.metadata.0.name
  depends_on         = [kubectl_manifest.argoeventswebhook]
}

###################
# install oauth2-proxy
###################


data "kubectl_path_documents" "oauth2" {
  pattern = "../../gateway/oauth2.yml"
  vars = {
    organization = var.organization
    # project      = var.project
  }
}
resource "kubectl_manifest" "oauth2" {
  count              = length(data.kubectl_path_documents.oauth2.documents)
  yaml_body          = element(data.kubectl_path_documents.oauth2.documents, count.index)
  override_namespace = kubernetes_namespace.serviceplane.metadata.0.name
  depends_on = [
    kubernetes_namespace.serviceplane, kubectl_manifest.oidcsecret
  ]
}

###################
# install main ui
###################

data "kubectl_path_documents" "mainui" {
  pattern = "../../adminapp/deployment.yml"
  vars = {
    registryprefix = var.registryprefix
    project        = var.project
    namespace      = kubernetes_namespace.serviceplane.metadata.0.name
  }
}
resource "kubectl_manifest" "mainui" {
  count              = 5 # length(data.kubectl_path_documents.mainui.documents)
  yaml_body          = element(data.kubectl_path_documents.mainui.documents, count.index)
  override_namespace = kubernetes_namespace.serviceplane.metadata.0.name
  depends_on = [
    kubernetes_namespace.serviceplane
  ]
}

###################
# install API
###################

data "kubectl_path_documents" "restapi" {
  pattern = "../../api/deployment.yml"
  vars = {
    registryprefix  = var.registryprefix
    project         = var.project
    namespace       = kubernetes_namespace.sparkplane.metadata.0.name
    firestoreviewer = kubernetes_service_account.firestoreviewer.metadata.0.name
    dataconfigargo  = kubernetes_config_map.usefuldataargo.metadata.0.name
  }
}
resource "kubectl_manifest" "restapi" {
  count              = 2 # length(data.kubectl_path_documents.restapi.documents)
  yaml_body          = element(data.kubectl_path_documents.restapi.documents, count.index)
  override_namespace = kubernetes_namespace.serviceplane.metadata.0.name
  depends_on = [
    kubernetes_namespace.serviceplane
  ]
}

###############
# install gateway
##############

data "kubectl_path_documents" "ingress" {
  pattern = "../../gateway/ingress.yml"
  vars = {
    organization = var.organization
    # project      = var.project
  }
}
resource "kubectl_manifest" "ingress" {
  count              = length(data.kubectl_path_documents.ingress.documents)
  yaml_body          = element(data.kubectl_path_documents.ingress.documents, count.index)
  override_namespace = kubernetes_namespace.serviceplane.metadata.0.name
  depends_on = [
    kubectl_manifest.argoeventswebhook,
    helm_release.grafana,
    helm_release.prometheus,
    kubectl_manifest.oauth2,
    kubectl_manifest.mainui
  ]
}


#################
# Install spark service monitor
#################


data "kubectl_path_documents" "servicemonitor" {
  pattern = "../../monitoring/servicemonitor.yml"
  vars = {
    sparknamepace       = kubernetes_namespace.sparkplane.metadata.0.name
    monitoringnamespace = kubernetes_namespace.serviceplane.metadata.0.name
  }
}
resource "kubectl_manifest" "servicemonitor" {
  count     = 1 #2 #length(data.kubectl_path_documents.servicemonitor.documents)
  yaml_body = element(data.kubectl_path_documents.servicemonitor.documents, count.index)
  #override_namespace = kubernetes_namespace.sparkplane.metadata.0.name
  depends_on = [
    # kubernetes_namespace.sparkplane,
    helm_release.prometheus,
  ]
}
