resource "google_endpoints_service" "openapi_service" {
  service_name = local.realoptions_gateway_url
  project      = var.project
  openapi_config = templatefile(
    "../../swagger/openapi.yml",
    {
      PROJECT_ID = var.project
      CLUSTER_IP = var.clusterip
    }
  )

}


