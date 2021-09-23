output "nameservers" {
  value = google_dns_managed_zone.streamstate-zone.name_servers
}
