variable "organization" {
  type = string
}
variable "project" {
  type = string
}
# this is likely a per-organization bucket
# TODO probably need to subsitute prefix at runtime
# so each organization gets own "backend"
terraform {
  backend "gcs" {
    bucket = "terraform-state-streamstate"
    prefix = "terraform/state-organization"
  }
}

# not actually sure what this is used for...
resource "google_service_account" "default" {
  project      = var.project
  account_id   = "service-account-id-${var.organization}"
  display_name = "Service Account ${var.organization}"
}

# eventually this should be a per project/app, and created via rest api?
# open question, do I want to deploy gcp resources through rest, or should
# we just have a single service account per org on the back end
resource "google_service_account" "spark-gcs" {
  project      = var.project
  account_id   = "spark-gcs"
  display_name = "spark-gcs"
}

# eventually this should be a per project
resource "google_storage_bucket" "sparkstorage" {
  project                     = var.project
  name                        = "streamstate-sparkstorage"
  location                    = "US"
  force_destroy               = true
  uniform_bucket_level_access = true
}

# eventually this should be a per project
resource "google_storage_bucket_iam_member" "sparkadmin" {
  bucket = google_storage_bucket.sparkstorage.name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.spark-gcs.account_id}@${var.project}.iam.gserviceaccount.com"
}

# eventually this should be a per project
resource "google_storage_bucket_iam_member" "clusterrole" {
  bucket = google_storage_bucket.sparkstorage.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.default.account_id}@${var.project}.iam.gserviceaccount.com"
}

# eventually this should be a per project
resource "google_project_iam_member" "containerpolicy" {
  project = var.project
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.spark-gcs.account_id}@${var.project}.iam.gserviceaccount.com"
}

# this should be at the organization level (each organization gets their own cluster)
resource "google_container_cluster" "primary" {
  project  = var.project
  name     = "streamstatecluster"
  location = "us-central1"

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
    service_account = google_service_account.default.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}
