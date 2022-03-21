provider "google" {
  project = var.project
  region  = var.region
}

# this is the default cluster service account, this shouldn't be used for much
# we should create custom service accounts with minimal permissions
resource "google_service_account" "cluster" {
  project      = var.project
  account_id   = "service-account-id-${var.organization}"
  display_name = "Service Account ${var.organization}"
}

# this should be at the global level, multitenant
resource "google_container_cluster" "primary" {
  project  = var.project
  name     = "streamstatecluster-${var.organization}"
  location = var.region
  release_channel {
    channel = "RAPID" # "REGULAR"  
  }
  # VPC-native
  network    = "default"
  subnetwork = "default"
  ip_allocation_policy {
    cluster_ipv4_cidr_block  = "/16"
    services_ipv4_cidr_block = "/22"
  }
  enable_autopilot = true
  /*identity_service_config {
    enabled=true
  }*/
}

data "google_container_cluster" "primary" {
  name     = google_container_cluster.primary.name
  location = var.region
}
resource "google_artifact_registry_repository_iam_member" "read" {
  provider   = google-beta
  project    = var.project
  location   = "us-central1"
  repository = var.project # see ../../global/global.tf
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.cluster.email}"
}



