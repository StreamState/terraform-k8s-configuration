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

resource "google_project_service" "resource_manager" {
  project = var.project
  service = "cloudresourcemanager.googleapis.com"
}

resource "google_project_service" "endpoints" {
  project = var.project
  service = "endpoints.googleapis.com"
}

resource "google_project_service" "iam" {
  project    = var.project
  service    = "iam.googleapis.com"
  depends_on = [google_project_service.resource_manager]
}
resource "google_project_service" "artifactregistry" {
  project    = var.project
  service    = "artifactregistry.googleapis.com"
  depends_on = [google_project_service.resource_manager]
}
resource "google_project_service" "registry" {
  project    = var.project
  service    = "containerregistry.googleapis.com"
  depends_on = [google_project_service.resource_manager]
}
resource "google_project_service" "container_cluster" {
  project    = var.project
  service    = "container.googleapis.com"
  depends_on = [google_project_service.resource_manager]
}

resource "google_artifact_registry_repository" "orgrepo" {
  provider      = google-beta
  project       = var.project
  location      = "us-central1"
  repository_id = var.project
  description   = "organization specific docker repo"
  format        = "DOCKER"
  depends_on    = [google_project_service.artifactregistry]
}

