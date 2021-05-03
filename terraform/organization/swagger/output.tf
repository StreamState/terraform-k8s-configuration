output "service_name" {
  value = local.service_name
}
output "swagger" {
  value = data.template_file.swagger.rendered
}
