variable "kubernetes_version" {
  default = "1.18"
}

variable "workers_count" {
  default = "1"
}

variable "organization" {
  type = string
}
variable "project" {
  type = string
}

variable "region" {
  type = string
}
