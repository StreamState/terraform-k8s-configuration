locals {
  service_name = "streamstate-api.endpoints.${var.project}.cloud.goog"
}


resource "google_endpoints_service" "openapi_service" {
  service_name = local.service_name
  project      = var.project
  openapi_config = templatefile(
    "../../swagger/openapi.yml",
    {
      PROJECT_ID = var.project
      CLUSTER_IP = var.clusterip
      HOST       = local.service_name
    }
  )

}


