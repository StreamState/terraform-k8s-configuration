# install gcloud and kubectl for gcloud

* https://cloud.google.com/kubernetes-engine/docs/quickstart#standard
* gcloud components install kubectl

See https://cloud.google.com/community/tutorials/managing-gcp-projects-with-terraform


* cd terraform
* export PROJECT_NAME=streamstatetest
* export TF_CREDS=~/.config/gcloud/${USER}-terraform-admin.json
* export BILLING_ACCOUNT=$(cat account_id) # this needs to be created, found via `gcloud alpha billing accounts list`
* gcloud projects create ${PROJECT_NAME}  --set-as-default
* gcloud iam service-accounts create terraform --display-name "Terraform admin account"
* gcloud iam service-accounts keys create ${TF_CREDS} --iam-account terraform@${PROJECT_NAME}.iam.gserviceaccount.com
* gcloud projects add-iam-policy-binding ${PROJECT_NAME} --member serviceAccount:terraform@${PROJECT_NAME}.iam.gserviceaccount.com --role roles/owner
* gcloud beta billing projects link $PROJECT_NAME --billing-account=$BILLING_ACCOUNT
* export GOOGLE_APPLICATION_CREDENTIALS=${TF_CREDS}


# using terraform
* gsutil mb -p $PROJECT_NAME gs://terraform-state-streamstate
Enable the Cloud Resource Manager through the GCP ui :|
* terraform init
* terraform apply -var="project=$PROJECT_NAME"
* helm install my-release spark-operator/spark-operator --namespace spark-operator --create-namespace

* sudo docker build .  -f ./sparkstreaming/Dockerfile -t gcr.io/$PROJECT/streamstate -t gcr.io/$PROJECT/streamstate:v0.1.0
* cat terraform/admin.json | sudo docker login -u _json_key --password-stdin https://gcr.io
* sudo docker push gcr.io/$PROJECT/streamstate
* sudo docker push gcr.io/$PROJECT/streamstate:v0.1.0



* kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/spark-on-k8s-operator/master/manifest/spark-rbac.yaml
* kubectl apply -f gke/example_gcp_k8s.yml


