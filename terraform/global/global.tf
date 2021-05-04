variable "project" {
  type = string
  #default = "streamstate"
}
variable "location" {
  type        = string
  description = "The default App Engine region. For instance 'europe-west'"
  default     = "us-central1"
}

terraform {
  backend "gcs" {
    bucket = "terraform-state-streamstate"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project
  region  = var.location
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

resource "google_project_service" "dns" {
  project = var.project
  service = "dns.googleapis.com"
  disable_dependent_services=true
}


resource "google_project_service" "firestore" {
  service                    = "firestore.googleapis.com"
  disable_dependent_services = true
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
  location      = var.location
  repository_id = var.project
  description   = "organization specific docker repo"
  format        = "DOCKER"
  depends_on    = [google_project_service.artifactregistry]
}

