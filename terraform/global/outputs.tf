output "nameservers" {
  value = google_dns_managed_zone.streamstate-zone.name_servers
}

output "staticip_name" {
  value = google_compute_global_address.staticgkeip.name
}

#output "swagger" {
#  value = module.swagger.swagger
#}
