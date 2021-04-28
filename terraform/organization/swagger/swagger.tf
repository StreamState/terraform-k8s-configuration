locals {
  service_name = "streamstate-api.endpoints.${var.project}.cloud.goog"
}

data "template_file" "swagger" {
  template = file("../../swagger/openapi.yml")
  vars = {
    CLUSTER_IP = var.clusterip
    HOST       = local.service_name
  }
}

resource "google_endpoints_service" "openapi_service" {
  service_name   = local.service_name
  project        = var.project
  openapi_config = data.template_file.swagger.rendered
}


