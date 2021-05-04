output "kubeconfig_path" {
  value = abspath("${path.root}/kubeconfig")
}

output "cluster_name" {
  value = module.gke-cluster.cluster_name
}

#output "swagger" {
#  value = module.swagger.swagger
#}

output "nameservers" {
  value = module.gke-cluster.nameservers
}
