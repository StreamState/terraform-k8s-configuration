provider "google" {
  project = var.project
  region  = var.region
  #zone    = "us-central1-c"
}

# this is the default cluster service account, this shouldn't be used for much
# we should create custom service accounts with minimal permissions
resource "google_service_account" "cluster" {
  project      = var.project
  account_id   = "service-account-id-${var.organization}"
  display_name = "Service Account ${var.organization}"
}

# this should be at the organization level (each organization gets their own cluster)
resource "google_container_cluster" "primary" {
  project  = var.project
  name     = "streamstatecluster-${var.organization}"
  location = var.region
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
  location   = var.region
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
      "https://www.googleapis.com/auth/cloud-platform",
    ]
  }
}

#resource "google_storage_bucket_iam_member" "viewer" {
#  bucket = "artifacts.${var.project}.appspot.com"
#  role   = "roles/storage.objectViewer"
#  member = "serviceAccount:${google_service_account.cluster.email}"
#}

resource "google_storage_bucket_iam_member" "writer" {
  bucket = "artifacts.${var.project}.appspot.com"
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cluster.email}"
}
