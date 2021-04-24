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
resource "kubernetes_namespace" "mainnamespace" {
  metadata {
    name = var.namespace
  }
  depends_on = [local_file.kubeconfig]
}

resource "kubernetes_namespace" "argoevents" {
  metadata {
    name = "argo-events"
  }
  depends_on = [local_file.kubeconfig]
}

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
  }
  depends_on = [local_file.kubeconfig]
}
##################
# Map GCP service accounts to kubernetes service accounts
##################


# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# this works with google service account binding to connect kubernetes and google accounts
resource "kubernetes_service_account" "docker-cfg-write-events" {
  metadata {
    name      = "docker-cfg-write"
    namespace = kubernetes_namespace.argoevents.metadata.0.name
    annotations = {
      "iam.gke.io/gcp-service-account" = var.docker_write_svc_email
    }
  }
  depends_on = [kubernetes_namespace.argoevents]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "bind_docker_write_argo" {
  service_account_id = var.docker_write_svc_name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${kubernetes_namespace.argoevents.metadata.0.name}/${kubernetes_service_account.docker-cfg-write-events.metadata.0.name}]",
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
    namespace = kubernetes_namespace.monitoring.metadata.0.name
    annotations = {
      "iam.gke.io/gcp-service-account" = var.spark_history_svc_email # todo, change this name
    }
  }
  depends_on = [kubernetes_namespace.monitoring]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "monitoring" {
  service_account_id = var.spark_history_svc_name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${kubernetes_namespace.monitoring.metadata.0.name}/${kubernetes_service_account.monitoring.metadata.0.name}]",
  ]
  depends_on = [
    kubernetes_service_account.monitoring
  ]
}



# use this for running steps in argo
resource "kubernetes_role" "argorules" {
  metadata {
    name      = "argoroles"
    namespace = kubernetes_namespace.argoevents.metadata.0.name
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
  depends_on = [kubernetes_namespace.argoevents]
}

resource "kubernetes_role_binding" "dockerwrite" {
  metadata {
    name      = "dockerwriteargopermissions-role-binding"
    namespace = kubernetes_namespace.argoevents.metadata.0.name
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.argorules.metadata.0.name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.docker-cfg-write-events.metadata.0.name
    namespace = kubernetes_namespace.argoevents.metadata.0.name
  }
}



resource "kubernetes_service_account" "spark" {
  metadata {
    name      = "spark"
    namespace = kubernetes_namespace.mainnamespace.metadata.0.name
  }
  depends_on = [kubernetes_namespace.mainnamespace]
}

## open question, should I use workload identity for creating folder or re-use the key?
## need to create explicit account for spark rather than workload identity for spark operator
resource "google_service_account_key" "sparkkey" {
  service_account_id = var.spark_gcs_svc_name
}

resource "kubernetes_secret" "spark-gcs-to-kubernetes" {
  metadata {
    name      = "spark-secret"
    namespace = kubernetes_namespace.mainnamespace.metadata.0.name
  }
  data = {
    "key.json" = base64decode(google_service_account_key.sparkkey.private_key)
  }
}



## needed for operating spark resources
resource "kubernetes_role" "sparkrules" {
  metadata {
    name      = "sparkrules"
    namespace = kubernetes_namespace.mainnamespace.metadata.0.name
  }
  rule {
    api_groups = [""]
    resources  = ["pods", "configmaps"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }
  depends_on = [kubernetes_namespace.mainnamespace]
}

resource "kubernetes_role_binding" "sparkrules" {
  metadata {
    name      = "sparkrules-role-binding"
    namespace = kubernetes_namespace.mainnamespace.metadata.0.name
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.sparkrules.metadata.0.name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.spark.metadata.0.name
    namespace = kubernetes_namespace.mainnamespace.metadata.0.name
  }
  depends_on = [kubernetes_namespace.mainnamespace]
}




##################
# Standalone kubernetes service accounts and secrets
##################


resource "random_password" "cassandra_password" {
  length  = 32
  special = true
}

resource "random_string" "cassandra_userid" {
  length  = 8
  special = false
}

locals {
  username = random_string.cassandra_userid.result
  password = random_password.cassandra_password.result
}

resource "kubernetes_secret" "cassandra_svc" {
  metadata {
    name      = "cassandra-secret"
    namespace = kubernetes_namespace.mainnamespace.metadata.0.name
  }
  data = {
    username = local.username
    password = local.password
  }
  type       = "kubernetes.io/generic"
  depends_on = [kubernetes_namespace.mainnamespace]
}

resource "kubernetes_secret" "cassandra_svcargo" {
  metadata {
    name      = "cassandra-secret"
    namespace = kubernetes_namespace.argoevents.metadata.0.name
  }
  data = {
    username = local.username
    password = local.password
  }
  type       = "kubernetes.io/generic"
  depends_on = [kubernetes_namespace.argoevents]
}

#resource "kubernetes_service_account" "cassandra_svc" {
#  metadata {
#    name      = "cassandra-svc"
#    namespace = kubernetes_namespace.mainnamespace.metadata.0.name
#  }

#  secret {
#    name = kubernetes_secret.cassandra_svc.metadata.0.name
#  }
#  depends_on = [kubernetes_namespace.mainnamespace]
#}

# this will have worklow permissions 
resource "kubernetes_service_account" "argoevents-runsa" {
  metadata {
    name      = "argoevents-runsa"
    namespace = kubernetes_namespace.argoevents.metadata.0.name
  }
  depends_on = [kubernetes_namespace.argoevents]
}

resource "kubernetes_role_binding" "argoevents-runrb" {
  metadata {
    name      = "argoevents-runsa-role-binding"
    namespace = kubernetes_namespace.argoevents.metadata.0.name
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.argorules.metadata.0.name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.argoevents-runsa.metadata.0.name
    namespace = kubernetes_namespace.argoevents.metadata.0.name
  }
  depends_on = [kubernetes_namespace.argoevents]
}

resource "kubernetes_service_account" "argoevents-sparksubmit" {
  metadata {
    name      = "argoevents-sparksubmit"
    namespace = kubernetes_namespace.argoevents.metadata.0.name
  }
  depends_on = [
    kubernetes_namespace.argoevents
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
  depends_on = [kubernetes_namespace.argoevents]
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
    namespace = kubernetes_namespace.argoevents.metadata.0.name # is this for the service account?  I think so...
  }
  depends_on = [kubernetes_namespace.argoevents]
}

##################
# Install Cassandra
##################

resource "helm_release" "cassandra" {
  name             = "cass-operator"
  namespace        = "cass-operator"
  create_namespace = true
  repository       = "https://datastax.github.io/charts"
  chart            = "cass-operator"

  set {
    name  = "clusterWideInstall"
    value = true
  }
  depends_on = [local_file.kubeconfig]
}

data "kubectl_file_documents" "cassandra" {
  content = templatefile("../../gke/cassandra.yml", {
    secret                 = kubernetes_secret.cassandra_svc.metadata.0.name,
    data_center            = var.data_center,
    cassandra_cluster_name = var.cassandra_cluster_name
  })
}

resource "kubernetes_config_map" "usefuldata" {
  metadata {
    name      = "sparkjobdata"
    namespace = kubernetes_namespace.mainnamespace.metadata.0.name
  }

  data = {
    data_center            = var.data_center
    cassandra_cluster_name = var.cassandra_cluster_name
    port                   = "9042"
    organization           = var.organization # may not need this, could pass this in
    project                = var.project
    org_bucket             = var.spark_storage_bucket_url
    # add checkpoint location here...
    spark_namespace = kubernetes_namespace.mainnamespace.metadata.0.name
  }

  depends_on = [kubernetes_namespace.mainnamespace]
}
resource "kubernetes_config_map" "usefuldataargo" {
  metadata {
    name      = "sparkjobdata"
    namespace = kubernetes_namespace.argoevents.metadata.0.name
  }

  data = {
    data_center            = var.data_center
    cassandra_cluster_name = var.cassandra_cluster_name
    port                   = "9042"
    organization           = var.organization
    project                = var.project
    org_bucket             = var.spark_storage_bucket_url
    # add checkpoint location here...
    spark_namespace = kubernetes_namespace.mainnamespace.metadata.0.name
  }

  depends_on = [kubernetes_namespace.argoevents, kubernetes_namespace.mainnamespace]
}

resource "kubectl_manifest" "cassandra" {
  count              = 3 # length(data.kubectl_file_documents.cassandra.documents)
  yaml_body          = element(data.kubectl_file_documents.cassandra.documents, count.index)
  override_namespace = kubernetes_namespace.mainnamespace.metadata.0.name
  depends_on         = [helm_release.cassandra]
}

##################
# Install Spark
##################
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
  depends_on = [local_file.kubeconfig] # needed to ensure that this gets destroyed in right order, dont think this works
}

##################
# Install Prometheus
##################
resource "helm_release" "prometheus" {
  name      = "prometheus"
  namespace = kubernetes_namespace.monitoring.metadata.0.name
  #create_namespace = true
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack" # apparently this includes the prometheus operator, while raw "prometheus" doesn't

  depends_on = [kubernetes_service_account.monitoring]
}


##################
# Install Argo
##################


data "kubectl_file_documents" "argoworkflow" {
  content = file("../../argo/argoinstall.yml")
}
resource "kubectl_manifest" "argoworkflow" {
  count              = length(data.kubectl_file_documents.argoworkflow.documents)
  yaml_body          = element(data.kubectl_file_documents.argoworkflow.documents, count.index)
  override_namespace = kubernetes_namespace.argoevents.metadata.0.name
  depends_on         = [kubernetes_namespace.argoevents]
}

data "kubectl_file_documents" "argoevents" {
  content = file("../../argo/argoeventsinstall.yml")
}

resource "kubectl_manifest" "argoevents" {
  count              = length(data.kubectl_file_documents.argoevents.documents)
  yaml_body          = element(data.kubectl_file_documents.argoevents.documents, count.index)
  override_namespace = kubernetes_namespace.argoevents.metadata.0.name
  depends_on         = [kubectl_manifest.argoworkflow]
}

data "kubectl_file_documents" "argoeventswebhook" {
  content = file("../../argo/webhookinstall.yml")
}

resource "kubectl_manifest" "argoeventswebhook" {
  count              = length(data.kubectl_file_documents.argoeventswebhook.documents)
  yaml_body          = element(data.kubectl_file_documents.argoeventswebhook.documents, count.index)
  override_namespace = kubernetes_namespace.argoevents.metadata.0.name
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
    cassandrasecret           = kubernetes_secret.cassandra_svc.metadata.0.name
    cassandrasecretargo       = kubernetes_secret.cassandra_svcargo.metadata.0.name
    dataconfig                = kubernetes_config_map.usefuldata.metadata.0.name
    dataconfigargo            = kubernetes_config_map.usefuldataargo.metadata.0.name
    namespace                 = kubernetes_namespace.mainnamespace.metadata.0.name

  })
}

resource "kubectl_manifest" "pysparkeventworkflow" {
  count              = 1
  yaml_body          = element(data.kubectl_file_documents.pysparkeventworkflow.documents, count.index)
  override_namespace = kubernetes_namespace.argoevents.metadata.0.name
  depends_on         = [kubectl_manifest.argoeventswebhook]
}

