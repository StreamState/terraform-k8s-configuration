terraform {
  required_version = ">= 0.13"
  required_providers {
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = ">= 1.7.0"
    }
  }
}


##################
# Set up connection to GKE
##################
data "google_client_config" "default" {
}

provider "helm" {
  kubernetes {
    host                   = var.cluster_endpoint
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(var.cluster_ca_cert)
  }
}

data "template_file" "kubeconfig" {
  template = file("${path.module}/kubeconfig.yml")

  vars = {
    cluster_name  = var.cluster_name
    endpoint      = var.cluster_endpoint
    cluster_ca    = var.cluster_ca_cert
    cluster_token = data.google_client_config.default.access_token
  }
}
# I believe this is needed to persist auth for more than 60 minutes
# careful!  this is sensitive, I believe
resource "local_file" "kubeconfig" {
  depends_on = [var.cluster_id]
  content    = data.template_file.kubeconfig.rendered
  filename   = "${path.root}/kubeconfig"
}

locals {
  controlpanenamespace          = "serviceplane-${var.organization}"
  sparknamespace                = "${var.namespace}-${var.organization}"
  dockerwriteserviceaccount     = "docker-write"
  sparkhistoryserviceaccount    = "spark-history"
  sparkserviceaccount           = "spark"
  argoserviceaccount            = "argo-service-account"
  firestoreserviceaccount       = "firestore"
  firestoreviewerserviceaccount = "firestore_viewer"
  dnsserviceaccount             = "cert-manager"

}
resource "helm_release" "streamstate" {
  name  = "streamstate"
  chart = "../../streamstate"
  set {
    name  = "oauth.client_id"
    value = var.client_id
  }
  set {
    name  = "oauth.client_secret"
    value = var.client_secret
  }
  values = [
    "${templatefile("../../streamstate/values.yaml", {
      controlpanenamespace          = local.controlpanenamespace
      sparknamespace                = local.sparknamespace
      project                       = var.project
      organization                  = var.organization
      tag                           = "v0.0.3"
      registry                      = var.org_registry
      sparkhistoryserviceaccount    = local.sparkhistoryserviceaccount
      sparkserviceaccount           = local.sparkserviceaccount
      argoserviceaccount            = local.argoserviceaccount
      dockerwriteserviceaccount     = local.dockerwriteserviceaccount
      firestoreserviceaccount       = local.firestoreserviceaccount
      firestoreviewerserviceaccount = local.firestoreviewerserviceaccount
      dnsserviceaccount             = local.dnsserviceaccount
      gcp_sparkhistory_svc          = var.spark_history_svc_email
      gcp_argo_svc                  = var.argo_svc_email
      gcp_docker_svc                = var.docker_write_svc_email
      gcp_firestore_svc             = var.firestore_svc_email
      gcp_firestore_viewer_svc      = var.firestoreviewer_svc_email
      gcp_dns_svc                   = var.dns_svc_email
      gcp_spark_svc                 = var.spark_gcs_svc_email
      bucket_without_gs             = replace(var.spark_storage_bucket_url, "gs://", "")
      sparkhistoryname              = "spark-history-server/"
      DS_PROMETHEUS                 = "Prometheus" # dummy for grafana
    })}"
  ]
  depends_on = [helm_release.spark, helm_release.nginx]
}
##################
# Map GCP service accounts to kubernetes service accounts
##################


# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "bind_docker_write_argo" {
  service_account_id = var.docker_write_svc_name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${local.controlpanenamespace}/${local.dockerwriteserviceaccount}]",
  ]
  depends_on = [
    helm_release.streamstate
  ]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "spark-history" {
  service_account_id = var.spark_history_svc_name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${local.controlpanenamespace}/${local.sparkhistoryserviceaccount}]",
  ]
  depends_on = [
    helm_release.streamstate
  ]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "firestore" {
  service_account_id = var.firestore_svc_name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${local.controlpanenamespace}/${local.firestoreserviceaccount}]",
  ]
  depends_on = [
    helm_release.streamstate
  ]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "firestoreviewer" {
  service_account_id = var.firestoreviewer_svc_name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${local.controlpanenamespace}/${local.firestoreviewerserviceaccount}]",
  ]
  depends_on = [
    helm_release.streamstate
  ]
}

# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#gcloud
# link service account and kubernetes service account
resource "google_service_account_iam_binding" "spark" {
  service_account_id = var.spark_gcs_svc_name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project}.svc.id.goog[${local.sparknamespace}/${local.sparkserviceaccount}]",
  ]
  depends_on = [
    helm_release.streamstate
  ]
}

## This is neeeded if using dns in cert issuer
resource "google_service_account_iam_binding" "dns" {
  service_account_id = var.dns_svc_name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "serviceAccount:${var.project}.svc.id.goog[${local.controlpanenamespace}/${local.dnsserviceaccount}]",
  ]
  depends_on = [
    helm_release.streamstate //helm creates the service account for me
  ]
}


##################
# Install Spark
##################
##########
# Todo, this should be one per cluster
# We will be multi-tenant so this should be in its own environment
# Move this to the "global" section of kuberentes
##########
resource "helm_release" "spark" {
  name             = "spark-operator"
  namespace        = "spark-operator"
  create_namespace = true
  repository       = "https://googlecloudplatform.github.io/spark-on-k8s-operator"
  chart            = "spark-operator"
  set {
    name  = "webhook.enable"
    value = true
  }
  set {
    name  = "metrics.enable"
    value = false //local prometheus shouldn't scrape global operator
  }
  depends_on = [local_file.kubeconfig]
}


##################
# Install Nginx
##################
# Todo, this should be installed cluster wide
resource "helm_release" "nginx" {
  name             = "nginx-ingress"
  namespace        = "nginx"
  create_namespace = true
  #repository       = "https://helm.nginx.com/stable"
  repository = "https://kubernetes.github.io/ingress-nginx"
  #chart      = "nginx-ingress"
  chart   = "ingress-nginx"
  version = "3.34.0"
  values = [
    "${templatefile("./kubernetes/nginxvalues.yml", {
      static_ip_address = var.staticip_address
    })}"
  ]
  depends_on = [local_file.kubeconfig]
}
