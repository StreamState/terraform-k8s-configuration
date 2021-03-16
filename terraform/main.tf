variable "project" {
  type    = string
  default = "streamstate"
}

terraform {
  backend "gcs" {
    bucket = "terraform-state-streamstate"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project
  region  = "us-central1"
  #zone    = "us-central1-c"
}


resource "google_project_service" "resource_manager" {
  project                    = var.project
  service                    = "cloudresourcemanager.googleapis.com"
  disable_dependent_services = true
}

resource "google_project_service" "iam" {
  project                    = var.project
  service                    = "iam.googleapis.com"
  disable_dependent_services = true
  depends_on                 = [google_project_service.resource_manager]
}

resource "google_service_account" "default" {
  account_id   = "service-account-id"
  display_name = "Service Account"
  depends_on   = [google_project_service.iam]
}
resource "google_service_account" "spark-gcs" {
  account_id   = "spark-gcs"
  display_name = "spark-gcs"
  depends_on   = [google_project_service.iam]
}

resource "google_storage_bucket" "sparkstorage" {
  name                        = "streamstate-sparkstorage"
  location                    = "US"
  force_destroy               = true
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_iam_member" "sparkadmin" {
  bucket = google_storage_bucket.sparkstorage.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.spark-gcs.account_id}@${var.project}.iam.gserviceaccount.com"
}


resource "google_project_service" "registry" {
  project                    = var.project
  service                    = "containerregistry.googleapis.com"
  depends_on                 = [google_project_service.resource_manager]
  disable_dependent_services = true
}

resource "google_container_registry" "registry" {
  project    = var.project
  location   = "US"
  depends_on = [google_project_service.registry]
}

resource "google_storage_bucket_iam_member" "viewer" {
  bucket = google_container_registry.registry.id
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.spark-gcs.account_id}@${var.project}.iam.gserviceaccount.com"
}

resource "google_project_service" "container_cluster" {
  project                    = var.project
  service                    = "container.googleapis.com"
  depends_on                 = [google_project_service.resource_manager]
  disable_dependent_services = true
}

resource "google_container_cluster" "primary" {
  name     = "streamstatecluster"
  location = "us-central1"

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1
  depends_on               = [google_project_service.container_cluster]
}

resource "google_container_node_pool" "primary_preemptible_nodes" {
  name       = "streamstatepool"
  location   = "us-central1"
  cluster    = google_container_cluster.primary.name
  node_count = 1
  # initial_node_count = 2
  #autoscaling {
  #  min_node_count = 1
  #  max_node_count = 5
  #}
  node_config {
    preemptible  = true
    machine_type = "e2-standard-2" # "e2-medium"

    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    service_account = google_service_account.default.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
  depends_on = [google_project_service.container_cluster]
}
