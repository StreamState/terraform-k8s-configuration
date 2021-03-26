variable "organization" {
  type = string
}
variable "namespace" {
  type = string
}
variable "project" {
  type = string
}
variable "registry" {
  type    = string # eg gcr.io
  default = "gcr.io"
}
# this is likely a per-organization bucket
# TODO probably need to subsitute prefix at runtime
# so each organization gets own "backend"
terraform {
  backend "gcs" {
    bucket = "terraform-state-streamstate"
    prefix = "terraform/state-organization"
  }
  required_providers {
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = ">= 1.7.0"
    }
  }
}




# this is the default cluster service account, this shouldn't be used for much
# we should create custom service accounts with minimal permissions
resource "google_service_account" "cluster" {
  project      = var.project
  account_id   = "service-account-id-${var.organization}"
  display_name = "Service Account ${var.organization}"
}

# it would be nice for this to be per app, but may not be feasible 
# since may not be able to create service accounts per job.
# Remember...I want all gcp resources defined through TF
# this is the service acccount for spark jobs and 
# can write to spark storage
resource "google_service_account" "spark-gcs" {
  project      = var.project
  account_id   = "spark-gcs-${var.organization}"
  display_name = "Spark Service account ${var.organization}"
}

# This is for writing to gcr registry
# needed for argo to deploy container to gcr
resource "google_service_account" "docker-write" {
  project      = var.project
  account_id   = "docker-write-${var.organization}"
  display_name = "docker-write-${var.organization}"
}

# This is for reading from gcr registry
# needed for argo containers AND for spark jobs
resource "google_service_account" "docker-read" {
  project      = var.project
  account_id   = "docker-read-${var.organization}"
  display_name = "docker-read-${var.organization}"
}


# Each project will have a "folder" in here
resource "google_storage_bucket" "sparkstorage" {
  project                     = var.project
  name                        = "streamstate-sparkstorage-${var.organization}"
  location                    = "US"
  force_destroy               = true
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_iam_member" "sparkadmin" {
  bucket = google_storage_bucket.sparkstorage.name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.spark-gcs.account_id}@${var.project}.iam.gserviceaccount.com"
}

# eventually this should be a per project
# I think this was needed for argo, but lets create a new argo service account instead
#resource "google_storage_bucket_iam_member" "clusterrole" {
#  bucket = google_storage_bucket.sparkstorage.name
#  role   = "roles/storage.objectAdmin"
#  member = "serviceAccount:${google_service_account.cluster.account_id}@${var.project}.iam.gserviceaccount.com"
#}

# eventually this should be a per project
resource "google_project_iam_member" "containerpolicy" {
  project = var.project
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.spark-gcs.account_id}@${var.project}.iam.gserviceaccount.com"
}

# this should be at the organization level (each organization gets their own cluster)
resource "google_container_cluster" "primary" {
  project  = var.project
  name     = "streamstatecluster-${var.organization}"
  location = "us-central1"
  # Enable Workload Identity
  workload_identity_config {
    identity_namespace = "${var.project}.svc.id.goog"
  }
  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1
}

# this should be at the organization level (each organization gets their own cluster)
resource "google_container_node_pool" "primary_preemptible_nodes" {
  project    = var.project
  name       = "${var.project}pool-${var.organization}"
  location   = "us-central1"
  cluster    = google_container_cluster.primary.name
  node_count = 1 # it keeps giving me 3 nodes though
  # initial_node_count = 2
  #autoscaling {
  #  min_node_count = 1
  #  max_node_count = 5
  #}
  node_config {
    preemptible  = true
    machine_type = "e2-standard-2" #"e2-medium" 

    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    service_account = google_service_account.cluster.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

# Configure kubernetes provider with Oauth2 access token.
# https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/client_config
# This fetches a new token, which will expire in 1 hour.
data "google_client_config" "default" {
}

provider "kubernetes" {
  host                   = google_container_cluster.primary.endpoint
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
}
# todo, adjust this since it will be run from github actions
#provider "kubernetes" {
#  host = google_container_cluster.primary.endpoint ## not sure this is right
#token                  = google_container_cluster.primary.master_auth.0.client_key
#  client_key             = base64decode(google_container_cluster.primary.master_auth.0.client_key)
#  client_certificate     = base64decode(google_container_cluster.primary.master_auth.0.client_certificate)
#  cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
#}

provider "helm" {
  kubernetes {
    host                   = google_container_cluster.primary.endpoint
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
  }
}
provider "kubectl" {
  host                   = google_container_cluster.primary.endpoint
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
}
resource "kubernetes_namespace" "mainnamespace" {
  metadata {
    name = var.namespace
  }
  depends_on = [google_container_node_pool.primary_preemptible_nodes]
}

resource "kubernetes_namespace" "argoevents" {
  metadata {
    name = "argo-events"
  }
  depends_on = [google_container_node_pool.primary_preemptible_nodes]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# this works with google service account binding to connect kubernetes and google accounts
resource "kubernetes_secret" "docker_registry_write_argo" { # does this need to be a docker registry type??

  metadata {
    name      = "docker-cfg"
    namespace = kubernetes_namespace.argoevents.metadata.0.name
    annotations = {
      "iam.gke.io/gcp-service-account" = "${google_service_account.docker-write.account_id}@${var.project}.iam.gserviceaccount.com"
    }
  }
  depends_on = [kubernetes_namespace.argoevents]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "bind_docker_write" {
  service_account_id = google_service_account.docker-write.name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${kubernetes_namespace.argoevents.metadata.0.name}]",
  ]
  depends_on = [
    kubernetes_secret.docker_registry_write_argo
  ]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# this works with google service account binding to connect kubernetes and google accounts
resource "kubernetes_secret" "docker_registry_read" { # does this need to be a docker registry type??
  metadata {
    name      = "docker-cfg-read"
    namespace = kubernetes_namespace.mainnamespace.metadata.0.name
    annotations = {
      "iam.gke.io/gcp-service-account" = "${google_service_account.docker-read.account_id}@${var.project}.iam.gserviceaccount.com"
    }
  }
  depends_on = [kubernetes_namespace.mainnamespace]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "bind_docker_read" {
  service_account_id = google_service_account.docker-read.name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${kubernetes_namespace.mainnamespace.metadata.0.name}]",
  ]
  depends_on = [
    kubernetes_secret.docker_registry_read
  ]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# this works with google service account binding to connect kubernetes and google accounts
resource "kubernetes_secret" "docker_registry_read_argo" { # does this need to be a docker registry type??
  metadata {
    name      = "docker-cfg-read-events"
    namespace = kubernetes_namespace.argoevents.metadata.0.name
    annotations = {
      "iam.gke.io/gcp-service-account" = "${google_service_account.docker-read.account_id}@${var.project}.iam.gserviceaccount.com"
    }
  }
  depends_on = [kubernetes_namespace.mainnamespace]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "bind_docker_read_argo" {
  service_account_id = google_service_account.docker-read.name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${kubernetes_namespace.argoevents.metadata.0.name}]",
  ]
  depends_on = [
    kubernetes_secret.docker_registry_read_argo
  ]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# this works with google service account binding to connect kubernetes and google accounts
resource "kubernetes_secret" "spark-secret" {
  metadata {
    name      = "spark-secret"
    namespace = kubernetes_namespace.mainnamespace.metadata.0.name
    annotations = {
      "iam.gke.io/gcp-service-account" = "${google_service_account.spark-gcs.account_id}@${var.project}.iam.gserviceaccount.com"
    }
  }
  depends_on = [kubernetes_namespace.mainnamespace]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "bind_spark_svc" {
  service_account_id = google_service_account.spark-gcs.name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${var.organization}]",
  ]
  depends_on = [
    kubernetes_secret.spark-secret
  ]
}

resource "random_password" "cassandra_password" {
  length     = 16
  special    = true
  depends_on = [google_container_node_pool.primary_preemptible_nodes]
}

resource "random_string" "cassandra_userid" {
  length     = 8
  special    = false
  depends_on = [google_container_node_pool.primary_preemptible_nodes]
}
resource "kubernetes_secret" "cassandra_svc" {
  metadata {
    name      = "cassandra-secret"
    namespace = kubernetes_namespace.mainnamespace.metadata.0.name
  }
  data = {
    username = random_string.cassandra_userid.result
    password = random_password.cassandra_password.result
  }
  type = "kubernetes.io/generic"
}

resource "kubernetes_service_account" "cassandra_svc" {
  metadata {
    name      = "cassandra-svc"
    namespace = kubernetes_namespace.mainnamespace.metadata.0.name
  }

  secret {
    name = kubernetes_secret.cassandra_svc.metadata.0.name
  }
}

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
  depends_on = [google_container_node_pool.primary_preemptible_nodes]
}


resource "helm_release" "spark" {
  name             = "spark-operator"
  namespace        = "spark-operator"
  create_namespace = true
  repository       = "https://googlecloudplatform.github.io/spark-on-k8s-operator"
  chart            = "spark-operator"

  depends_on = [google_container_node_pool.primary_preemptible_nodes]
}

data "kubectl_file_documents" "cassandra" {
  content = templatefile("../../gke/cassandra.yml", { secret = kubernetes_secret.cassandra_svc.metadata.0.name })
}

resource "kubectl_manifest" "cassandra" {
  count              = length(data.kubectl_file_documents.cassandra.documents)
  yaml_body          = element(data.kubectl_file_documents.cassandra.documents, count.index)
  override_namespace = kubernetes_namespace.mainnamespace.metadata.0.name
  depends_on         = [helm_release.cassandra]
}

data "kubectl_file_documents" "argoworkflow" {
  content = file("../../argo/argoinstall.yml")
}
resource "kubectl_manifest" "argoworkflow" {
  count     = length(data.kubectl_file_documents.argoworkflow.documents)
  yaml_body = element(data.kubectl_file_documents.argoworkflow.documents, count.index)
  #yaml_body          = file("../../argo/argoinstall.yml")
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

data "kubectl_file_documents" "argoeventworkflow" {
  content = templatefile("../../argo/eventworkflow.yml", {
    project           = var.project,
    dockersecretwrite = kubernetes_secret.docker_registry_write_argo.metadata.0.name,
    dockersecretread  = kubernetes_secret.docker_registry_read_argo.metadata.0.name,
    registry          = var.registry
  })
}
## The docker containers needed for this are built as part of the CI/CD pipeline that
## includes provisioning global TF, so the images will be available
## question: which images?  The latest?  Or specific tags?
resource "kubectl_manifest" "argoeventworkflow" {
  count              = length(data.kubectl_file_documents.argoeventworkflow.documents)
  yaml_body          = element(data.kubectl_file_documents.argoeventworkflow.documents, count.index)
  override_namespace = kubernetes_namespace.argoevents.metadata.0.name
  depends_on         = [kubectl_manifest.argoevents]
}
