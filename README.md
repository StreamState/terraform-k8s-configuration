
# helpful commands for teraform
* terraform state rm 'module.kubernetes-config'
* kubectl --kubeconfig terraform/organization/kubeconfig -n argo-events get pods

# install gcloud and kubectl for gcloud

* https://cloud.google.com/kubernetes-engine/docs/quickstart#standard
* gcloud components install kubectl

See https://cloud.google.com/community/tutorials/managing-gcp-projects-with-terraform


* cd terraform/organization
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
* terraform apply -var-file="testing.tfvars"
* (direct connection with kubectl): gcloud container clusters get-credentials streamstatecluster-testorg --region=us-central1
* (connection through terraform kubeconfig): kubectl --kubeconfig terraform/organization/kubeconfig [etc]

To shut down:

* terraform destroy -var-file="testing.tfvars"

If anything hangs, you can delete the kubernetes module:

* terraform state rm 'module.kubernetes-config'


# setup for deploy

todo! make this part of CI/CD pipeline for the entire project (streamstate) level

* cd docker
* sudo docker build . -f ./sparkpy.Dockerfile -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/pysparkbase -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/pysparkbase:v0.1.0
* sudo docker push us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/pysparkbase:v0.1.0

* sudo docker build . -f ./sparktest.Dockerfile -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/pysparktest -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/pysparktest:v0.1.0
* sudo docker push us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/pysparktest:v0.1.0
* cd ..

* cd backendapp
* sudo docker build . -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/firestoresetup -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/firestoresetup:v0.1.0
* sudo docker push us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/firestoresetup:v0.1.0
* cd ..

# setup spark history server

* sudo docker build . -f ./spark-history/Dockerfile -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/sparkhistory -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/sparkhistory:v0.2.0
* sudo docker push us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/sparkhistory:v0.2.0

Unfortunately, this requires root access, but just for spark history which has very minimal permissions

# argo helps

To find webui url:
* kubectl port-forward svc/argo-server -n argo-events 2746:2746



# deploy workflow



* kubectl  -n argo-events port-forward $(kubectl -n argo-events get pod -l eventsource-name=streamstatewebservice -o name) 12000:12000 

* curl  -H "Content-Type: application/json" -X POST -d "{\"pythoncode\":\"$(base64 -w 0 examples/process.py)\", \"inputs\": $(cat examples/sampleinputs.json), \"assertions\": $(cat examples/assertedoutputs.json), \"kafka\": {\"brokers\": \"broker1,broker2\"}, \"outputs\": {\"mode\": \"append\", \"checkpoint_location\": \"/tmp/checkpoint\", \"processing_time\":\"2 seconds\"}, \"fileinfo\":{\"max_file_age\": \"2d\"}, \"table\":{\"primary_keys\":[\"field1\"], \"output_schema\":[{\"name\":\"field1\", \"type\": \"string\"}]}, \"appname\":\"mytestapp\"}" http://localhost:12000/build/container


TODO!  Open question: do I actually need a static IP address once I get the streamstate url working?  It almost looks like I don't need a static ip.  I needed a static IP only when using a GCP ingress: https://github.com/StreamState/k8s_poc/blob/c6355c4df52b215ef27349f88a8cf6d300274223/argo/webhookinstall.yml#L137.  I do think I need it permanently or else every time I undo it will have to wait 48 hours to propogate.  However, I don't need to pass the value in to kubernetes...it will just use the hostname.

TODO! I may need to use the "full" DNS host name (currently myzone.streamstate.org) rather than simply streamstate.org

nslookup myzone.streamstate.org
dig +trace myzone.streamstate.org

TODO! The gloo external IP address is NOT using the cluster address...is there a way to add the external address to the cluster at creation? https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_cluster

curl  -H "Content-Type: application/json" -X POST -d "{\"pythoncode\":\"$(base64 -w 0 examples/process.py)\", \"inputs\": $(cat examples/sampleinputs.json), \"assertions\": $(cat examples/assertedoutputs.json), \"kafka\": {\"brokers\": \"broker1,broker2\"}, \"outputs\": {\"mode\": \"append\", \"checkpoint_location\": \"/tmp/checkpoint\", \"processing_time\":\"2 seconds\"}, \"fileinfo\":{\"max_file_age\": \"2d\"}, \"table\":{\"primary_keys\":[\"field1\"], \"output_schema\":[{\"name\":\"field1\", \"type\": \"string\"}]}, \"appname\":\"mytestapp\"}" 34.98.95.203/build/container



# upload json to bucket

* kubectl apply -f gke/replay_from_file.yml
* echo {\"id\": 1,\"first_name\": \"John\", \"last_name\": \"Lindt\",  \"email\": \"jlindt@gmail.com\",\"gender\": \"Male\",\"ip_address\": \"1.2.3.4\"} >> ./mytest.json


You may have to create a subfolder first (eg, /test)

* gsutil cp ./mytest.json gs://streamstate-sparkstorage-testorg/test
* kubectl logs replaytest-driver
* kubectl port-forward examplegcp-driver 4040:4040 # to view spark-ui, go to localhost:4040


* echo {\"field1\": \"somevalue\"} > ./mytest1.json
* gsutil cp ./mytest1.json gs://streamstate-sparkstorage-testorg/mytestapp/topic1

# Backend service service 

The backend for provisioning new jobs


# dev area
* sudo docker build . -t spsbt -f ./test_container/Dockerfile
* sudo docker run -it spsbt /bin/bash
* spark-submit --master local[*] --class dhstest.FileSourceWrapper target/scala-2.12/kafka_and_file_connect.jar myapp ./tmp_file 0 Append /tmp
* sudo docker exec -it $(sudo -S docker ps -q  --filter ancestor=spsbt) /bin/bash
* echo {\"id\": 1,\"first_name\": \"John\", \"last_name\": \"Lindt\",  \"email\": \"jlindt@gmail.com\",\"gender\": \"Male\",\"ip_address\": \"1.2.3.4\"} >> ./tmp_file/mytest.json


# prometheus


* kubectl port-forward svc/prometheus-operated -n monitoring 9090:9090
* kubectl port-forward svc/prometheus-grafana  -n monitoring 8000:80

Grafana password:
* kubectl get secret --namespace monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode


# test workload identity

kubectl run -it \
--image google/cloud-sdk:slim \
--serviceaccount spark \
--namespace mainspark \
workload-identity-test

