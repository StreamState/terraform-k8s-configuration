# install gcloud and kubectl for gcloud

* https://cloud.google.com/kubernetes-engine/docs/quickstart#standard
* gcloud components install kubectl

See https://cloud.google.com/community/tutorials/managing-gcp-projects-with-terraform


* cd terraform
* export PROJECT_NAME=streamstatetest
* export ORGANIZATION_NAME=testorg
* export TF_CREDS=~/.config/gcloud/${USER}-terraform-admin.json
* export BILLING_ACCOUNT=$(cat account_id) # this needs to be created, found via `gcloud alpha billing accounts list`
* gcloud projects create ${PROJECT_NAME}  --set-as-default
* gcloud iam service-accounts create terraform --display-name "Terraform admin account"
* gcloud iam service-accounts keys create ${TF_CREDS} --iam-account terraform@${PROJECT_NAME}.iam.gserviceaccount.com
* gcloud projects add-iam-policy-binding ${PROJECT_NAME} --member serviceAccount:terraform@${PROJECT_NAME}.iam.gserviceaccount.com --role roles/owner
* gcloud beta billing projects link $PROJECT_NAME --billing-account=$BILLING_ACCOUNT
* export GOOGLE_APPLICATION_CREDENTIALS=${TF_CREDS}


# using terraform
Parts of this should be done once for streamstate, others should be organization and app specific.

Eventually we need a way for three seperate pipelines.  I suggest using github actions+Terraform for changes/updates to streamstate.  We may want github actions+Terraform for each organization as well...we can trigger a "terraform apply" when a company signs up, and a "terrafrom destroy" for when a company leaves.  We can also stand up an argo workflow locally to an organization for their pipelines...or should we assume they will byo and can simply provide a REST api for interaction?  

* gsutil mb -p $PROJECT_NAME gs://terraform-state-streamstate
Enable the Cloud Resource Manager through the GCP ui :

The global tf does NOT create expensive resources, and simply enables services

* cd global
* terraform init
* terraform apply -var="project=$PROJECT_NAME"
* cd ..
* cd organization
The organization tf creates expensive resources, so please destroy afterwards!
* terraform init
* terraform apply -var="organization=$ORGANIZATION_NAME" -var="project=$PROJECT_NAME"
* gcloud container clusters get-credentials streamstatecluster --zone us-central1 # if needed for helm
* helm install my-release spark-operator/spark-operator  --namespace spark-operator --create-namespace # --set enableWebhook=true
* cd .

# build and push the container
This should be done once for streamstate, and available to every organization
* sudo docker build .  -f ./sparkstreaming/Dockerfile -t us.gcr.io/$PROJECT_NAME/streamstate -t us.gcr.io/$PROJECT_NAME/streamstate:v0.1.0
* cat $TF_CREDS | sudo docker login -u _json_key --password-stdin https://us.gcr.io
* sudo docker push us.gcr.io/$PROJECT_NAME/streamstate
* sudo docker push us.gcr.io/$PROJECT_NAME/streamstate:v0.1.0

# create the spark application

This should be done at the project/app level

* gcloud iam service-accounts keys create key.json --iam-account spark-gcs@${PROJECT_NAME}.iam.gserviceaccount.com # eventually do this per app
* kubectl create secret generic spark-secret --from-file=key.json --save-config --dry-run=client  -o yaml | kubectl apply -f - 
* kubectl apply -f gke/spark-service-account.yml
* kubectl apply -f gke/example_gcp_k8s.yml

# upload json to bucket

* echo {\"id\": 1,\"first_name\": \"John\", \"last_name\": \"Lindt\",  \"email\": \"jlindt@gmail.com\",\"gender\": \"Male\",\"ip_address\": \"1.2.3.4\"} >> ./mytest.json
* gsutil cp ./mytest.json gs://streamstate-sparkstorage/
* kubectl logs examplegcp-driver
* kubectl port-forward examplegcp-driver 4040:4040 # to view spark-ui, go to localhost:4040

# Cassandra

This should be done at the organization level, with a table per project/app

* helm install cass-operator datastax/cass-operator  --namespace cass-operator --create-namespace
* kubectl -n cass-operator apply -f ./gke/cassandra.yaml