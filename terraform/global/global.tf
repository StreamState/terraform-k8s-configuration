variable "project" {
  type = string
  #default = "streamstate"
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


# TODO!  make this accessible by the spark service account (or service-account-id?) but not public
#resource "google_storage_bucket_iam_member" "viewer" {
#  bucket = google_container_registry.registry.id
#  role   = "roles/storage.objectViewer"
#  member = "allUsers"
#}

resource "google_project_service" "resource_manager" {
  project = var.project
  service = "cloudresourcemanager.googleapis.com"
}

resource "google_project_service" "iam" {
  project    = var.project
  service    = "iam.googleapis.com"
  depends_on = [google_project_service.resource_manager]
}
resource "google_project_service" "registry" {
  project    = var.project
  service    = "containerregistry.googleapis.com"
  depends_on = [google_project_service.resource_manager]
}

# destroying this does NOT destroy the bucket behind the scenes
# this will be a global repo for all organizations to access, though they won't explicitly know this
resource "google_container_registry" "registry" {
  project    = var.project
  location   = "US" # todo, make this NOT US
  depends_on = [google_project_service.registry]
}

resource "google_project_service" "container_cluster" {
  project    = var.project
  service    = "container.googleapis.com"
  depends_on = [google_project_service.resource_manager]
}
