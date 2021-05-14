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
resource "kubernetes_service_account" "monitoring" {
  metadata {
    name      = "monitoring"
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
    annotations = {
      "iam.gke.io/gcp-service-account" = var.spark_history_svc_email
    }
  }
  depends_on = [kubernetes_namespace.serviceplane]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "monitoring" {
  service_account_id = var.spark_history_svc_name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${kubernetes_namespace.serviceplane.metadata.0.name}/${kubernetes_service_account.monitoring.metadata.0.name}]",
  ]
  depends_on = [
    kubernetes_service_account.monitoring
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




##################
# Standalone kubernetes service accounts and secrets
##################

# this will have worklow permissions 
resource "kubernetes_service_account" "argoevents-runsa" {
  metadata {
    name      = "argoevents-runsa"
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
  }
  depends_on = [kubernetes_namespace.serviceplane]
}

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
    name      = kubernetes_service_account.argoevents-runsa.metadata.0.name
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
  }
  depends_on = [kubernetes_namespace.serviceplane]
}



resource "kubernetes_service_account" "argoevents-sparksubmit" {
  metadata {
    name      = "argoevents-sparksubmit"
    namespace = kubernetes_namespace.serviceplane.metadata.0.name
  }
  depends_on = [
    kubernetes_namespace.serviceplane
  ]
}
resource "kubernetes_cluster_role" "launchsparkoperator" {
  metadata {
    name = "launchsparkoperator-role"
  }
  rule {
    api_groups = ["sparkoperator.k8s.io"]
    resources  = ["sparkapplications"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }
  rule {
    api_groups = ["monitoring.coreos.com"]
    resources  = ["prometheuses", "servicemonitors"]
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
resource "kubernetes_cluster_role_binding" "launchsparkoperator" {
  metadata {
    name = "launchspark-role-binding"
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.launchsparkoperator.metadata.0.name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.argoevents-sparksubmit.metadata.0.name
    namespace = kubernetes_namespace.serviceplane.metadata.0.name # is this for the service account?  I think so...
  }
  depends_on = [kubernetes_namespace.serviceplane]
}


#### Data

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
# Install Password Generator
##################
resource "helm_release" "passwordgenerator" {
  name             = "kubernetes-secret-generator"
  namespace        = kubernetes_namespace.serviceplane.metadata.0.name //"passwordgenerate-${var.organization}"
  //create_namespace = true
  repository       = "https://helm.mittwald.de"
  chart            = "kubernetes-secret-generator"
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
/*
data "kubectl_file_documents" "oidcsecretmonitoring" {
  content = templatefile("../../gateway/oidc.yml", {
    client_id     = base64encode(var.client_id),
    client_secret = base64encode(var.client_secret)
  })
}
resource "kubectl_manifest" "oidcsecretmonitoring" {
  count              = 1
  yaml_body          = element(data.kubectl_file_documents.oidcsecretmonitoring.documents, count.index)
  override_namespace = kubernetes_namespace.monitoring.metadata.0.name
  depends_on         = [helm_release.passwordgenerator]
}*/



##################
# Install Prometheus
##################

data "kubectl_file_documents" "prometheusconfigs" {
  content = file("../../prometheus/configs.yml")
}
resource "kubectl_manifest" "prometheusconfigs" {
  count              = length(data.kubectl_file_documents.prometheusconfigs.documents)
  yaml_body          = element(data.kubectl_file_documents.prometheusconfigs.documents, count.index)
  override_namespace = kubernetes_namespace.serviceplane.metadata.0.name
  # depends_on         = [helm_release.passwordgenerator]
}
resource "helm_release" "prometheus" {
  name      = "prometheus"
  namespace = kubernetes_namespace.serviceplane.metadata.0.name
  //namespace  = "monitoring-${var.organization}" //kubernetes_namespace.monitoring.metadata.0.name
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus" # does not include prometheus operator
  //create_namespace=true
  /*set {
    name= "kubeStateMetrics.enabled"
    value=false
  }
  set {
    name= "server.enabled"
    value=false
  }*/
  values = [
    "${templatefile("../../prometheus/prometheus_helm_values.yml", {
      organization = var.organization
    })}"
  ]
  depends_on = [
    kubernetes_namespace.serviceplane,
    kubectl_manifest.prometheusconfigs,
    kubectl_manifest.oidcsecret
  ]
}

resource "helm_release" "grafana" {
  name       = "grafana"
  namespace  = kubernetes_namespace.serviceplane.metadata.0.name
  repository = "https://grafana.github.io/helm-charts"
  chart      = "grafana" # does not include prometheus operator
  values = [
    "${templatefile("../../prometheus/grafana_helm_values.yml", {
      organization = var.organization
    })}"
  ]
  depends_on = [
    kubernetes_namespace.serviceplane,
    kubectl_manifest.prometheusconfigs,
    kubectl_manifest.oidcsecret
  ]
}

/*
data "kubectl_path_documents" "prometheussetup" {
  pattern = "../../kube-prometheus/manifests/setup/*.yaml"
}

resource "kubectl_manifest" "prometheussetup" {
  count      = length(data.kubectl_path_documents.prometheussetup.documents)
  yaml_body  = element(data.kubectl_path_documents.prometheussetup.documents, count.index)
  depends_on = [kubernetes_namespace.argoevents, kubectl_manifest.oidcsecretargo]
}

data "kubectl_path_documents" "prometheusinstall" {
  pattern = "../../kube-prometheus/manifests/*.yaml"
}

resource "kubectl_manifest" "prometheusinstall" {
  count      = length(data.kubectl_path_documents.prometheusinstall.documents)
  yaml_body  = element(data.kubectl_path_documents.prometheusinstall.documents, count.index)
  depends_on = [kubectl_manifest.prometheussetup]
}*/


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


data "kubectl_file_documents" "argoworkflow" {
  content = templatefile("../../argo/argoinstall.yml", {
    organization=var.organization
  })
}
resource "kubectl_manifest" "argoworkflow" {
  count              = 17 # length(data.kubectl_file_documents.argoworkflow.documents)
  yaml_body          = element(data.kubectl_file_documents.argoworkflow.documents, count.index)
  override_namespace = kubernetes_namespace.serviceplane.metadata.0.name
  depends_on         = [kubernetes_namespace.serviceplane, kubectl_manifest.oidcsecret]
}

data "kubectl_file_documents" "argoevents" {
  content = file("../../argo/argoeventsinstall.yml")
}

resource "kubectl_manifest" "argoevents" {
  count              = length(data.kubectl_file_documents.argoevents.documents)
  yaml_body          = element(data.kubectl_file_documents.argoevents.documents, count.index)
  override_namespace = kubernetes_namespace.serviceplane.metadata.0.name
  depends_on         = [kubectl_manifest.argoworkflow]
}

data "kubectl_file_documents" "argoeventswebhook" {
  content = file("../../argo/webhookinstall.yml")
}

resource "kubectl_manifest" "argoeventswebhook" {
  count              = length(data.kubectl_file_documents.argoeventswebhook.documents)
  yaml_body          = element(data.kubectl_file_documents.argoeventswebhook.documents, count.index)
  override_namespace = kubernetes_namespace.serviceplane.metadata.0.name
  depends_on         = [kubectl_manifest.argoevents]
}

data "kubectl_file_documents" "pysparkeventworkflow" {
  content = templatefile("../../argo/pysparkworkflow.yml", {
    project                   = var.project,
    organization              = var.organization
    dockersecretwrite         = kubernetes_service_account.docker-cfg-write-events.metadata.0.name,
    registry                  = var.org_registry
    registryprefix            = var.registryprefix
    runserviceaccount         = kubernetes_service_account.argoevents-runsa.metadata.0.name
    sparksubmitserviceaccount = kubernetes_service_account.argoevents-sparksubmit.metadata.0.name
    sparkserviceaccount       = kubernetes_service_account.spark.metadata.0.name
    firestoreserviceaccount   = kubernetes_service_account.firestore.metadata.0.name
    dataconfig                = kubernetes_config_map.usefuldata.metadata.0.name
    dataconfigargo            = kubernetes_config_map.usefuldataargo.metadata.0.name
    namespace                 = kubernetes_namespace.sparkplane.metadata.0.name
    monitoringnamespace       = kubernetes_namespace.serviceplane.metadata.0.name

  })
}

resource "kubectl_manifest" "pysparkeventworkflow" {
  count              = 1
  yaml_body          = element(data.kubectl_file_documents.pysparkeventworkflow.documents, count.index)
  override_namespace = kubernetes_namespace.serviceplane.metadata.0.name
  depends_on         = [kubectl_manifest.argoeventswebhook]
}


###################
# Install servicemonitor for argo
###################
/*
data "kubectl_file_documents" "argoprometheus" {
  content = templatefile("../../prometheus/prometheus_argo.yml", {
    servicenamespace    = kubernetes_namespace.serviceplane.metadata.0.name
    monitoringnamespace = kubernetes_namespace.serviceplane.metadata.0.name
  })
}
resource "kubectl_manifest" "argoprometheus" {
  count      = 2
  yaml_body  = element(data.kubectl_file_documents.argoprometheus.documents, count.index)
  depends_on = [helm_release.prometheus, kubectl_manifest.pysparkeventworkflow]
}*/


###############
# install certs and gateway
##############


data "kubectl_file_documents" "ingress" {
  content = templatefile("../../gateway/ingress.yml", {
    organization = var.organization
  })
}
resource "kubectl_manifest" "ingress" {
  count              = 3 #length(data.kubectl_file_documents.ingress.documents)
  yaml_body          = element(data.kubectl_file_documents.ingress.documents, count.index)
  override_namespace = kubernetes_namespace.serviceplane.metadata.0.name
  depends_on = [
    kubectl_manifest.argoeventswebhook
  ]
}
