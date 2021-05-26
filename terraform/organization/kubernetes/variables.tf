variable "cluster_name" {
  type = string
}

variable "cluster_id" {
  type = string
}



variable "cluster_endpoint" {
  type = string
}

variable "cluster_ca_cert" {
  type = string
}

variable "project" {
  type = string
}

variable "organization" {
  type = string
}
variable "registryprefix" {
  type = string
}

variable "namespace" {
  type = string
}

variable "docker_write_svc_email" {
  type = string
}
variable "docker_write_svc_name" {
  type = string
}

variable "firestore_svc_name" {
  type = string
}
variable "firestore_svc_email" {
  type = string
}
variable "spark_gcs_svc_name" {
  type = string
}
variable "spark_gcs_svc_email" {
  type = string
}
variable "spark_history_svc_email" {
  type = string
}
variable "spark_history_svc_name" {
  type = string
}
variable "org_registry" {
  type = string
}
variable "spark_history_bucket_url" { # probably delete
  type = string
}
variable "spark_storage_bucket_url" {
  type = string
}

/*
variable "staticipname" {
  type = string
}
*/
variable "staticip_address" {
  type = string
}


variable "dns_svc_name" {
  type = string
}
variable "dns_svc_email" {
  type = string
}

variable "argo_svc_name" {
  type = string
}
variable "argo_svc_email" {
  type = string
}

//temporary, lets see if this actually works
//It does work!  Need to figure out what to make
//this programtic for organizations
variable "client_id" {
  type = string
}
variable "client_secret" {
  type = string
}

