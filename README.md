
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

# Cassandra

This is relevant if you really need to work directly with Cassandra; however the REST API client should be the primary way of interacting with Cassandra.

https://docs.datastax.com/en/cass-operator/doc/cass-operator/cassOperatorConnectWithinK8sCluster.html

* kubectl get secrets/cassandra-secret -n mainspark --template={{.data.password}} | base64 -d
* kubectl exec -n mainspark -i -t -c cassandra cluster1-dc1-default-sts-0 -- /opt/cassandra/bin/cqlsh -u $(kubectl get secrets/cassandra-secret -n mainspark --template={{.data.username}} | base64 -d) -p $(kubectl get secrets/cassandra-secret -n mainspark --template={{.data.password}} | base64 -d)


* CREATE KEYSPACE IF NOT EXISTS cycling WITH replication = { 'class' : 'NetworkTopologyStrategy', 'dc1' : '1' };
* CREATE TABLE IF NOT EXISTS cycling.cyclist_semi_pro (
   first_name text, 
   last_name text, 
   PRIMARY KEY (last_name));
* INSERT INTO cycling.cyclist_semi_pro (first_name, last_name) VALUES ('Carlos', 'Perotti');


* kubectl get pod cluster1-dc1-default-sts-0 --template='{{(index (index .spec.containers 0).ports 0).containerPort}}{{"\n"}}' -n mainspark
* kubectl port-forward pod/cluster1-dc1-default-sts-0 30500:9042 -n mainspark


# setup for deploy

todo! make this part of CI/CD pipeline for the entire project (streamstate) level
* cat $TF_CREDS | sudo docker login -u _json_key --password-stdin https://us-central1-docker.pkg.dev
* sudo docker build . -f ./argo/scalacompile.Dockerfile -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/scalacompile -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/scalacompile:v0.8.0
* sudo docker push us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/scalacompile:v0.8.0


* sudo docker build . -f ./argo/sparkbase.Dockerfile -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/sparkbase -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/sparkbase:v0.1.0 
* sudo docker push us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/sparkbase:v0.1.0


# setup spark history server

* sudo docker build . -f ./spark-history/Dockerfile -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/sparkhistory -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/sparkhistory:v0.2.0
* sudo docker push us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/sparkhistory:v0.2.0

Unfortunately, this requires root access, but just for spark history which has very minimal permissions

# argo helps

To find webui url:
* kubectl -n argo-events get svc
* go to [webuiurl]:2746 in your favorite browser



# deploy workflow

* kubectl  -n argo-events port-forward $(kubectl -n argo-events get pod -l eventsource-name=webhook -o name) 12000:12000 
* curl -H "Content-Type: application/json" -X POST -d "{\"scalacode\":\"$(base64 -w 0 ./src/main/scala/custom.scala)\"}" http://localhost:12000/build/container


* curl -H "Content-Type: application/json" -X POST -d "{\"scalacode\":\"$(base64 -w 0 ./src/main/scala/custom.scala)\"}" http://[ipaddress from load balancer]:12000/build/container 


# upload json to bucket

* kubectl apply -f gke/replay_from_file.yml
* echo {\"id\": 1,\"first_name\": \"John\", \"last_name\": \"Lindt\",  \"email\": \"jlindt@gmail.com\",\"gender\": \"Male\",\"ip_address\": \"1.2.3.4\"} >> ./mytest.json


You may have to create a subfolder first (eg, /test)

* gsutil cp ./mytest.json gs://streamstate-sparkstorage-testorg/test
* kubectl logs replaytest-driver
* kubectl port-forward examplegcp-driver 4040:4040 # to view spark-ui, go to localhost:4040


# python consume cassandra

* python3 -m venv env
* source env/bin/activate
* pip3 install -r ./pythonexample/requirements.txt
* python3 pythonexample/connect_cassandra.py

# Backend service service 

The backend for provisioning new jobs

## python rest app

* sudo docker build . -f backendapp/Dockerfile -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/rest -t us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/rest:v0.16.0
* sudo docker push us-central1-docker.pkg.dev/$PROJECT_NAME/streamstatetest/rest:v0.16.0
* [do something here with ingress]

After everything is provisioned, run the following:
34.68.82.248
curl 34.68.82.248:8000/database/create  -X POST 
export AVRO_SCHEMA='{"name": "testapp", "type":"record", "doc": "testavro", "fields":[{"name": "first_name", "type":"string"}, {"name":"last_name", "type":"string"}]}'
curl 34.68.82.248:8000/database/table/update  -X POST -d "{\"organization\": \"$ORGANIZATION_NAME\", \"avro_schema\":$AVRO_SCHEMA, \"primary_keys\":[\"last_name\"] }"

curl 34.68.82.248:8000/job/replay  -X POST -d "{\"organization\": \"$ORGANIZATION_NAME\", \"avro_schema\":$AVRO_SCHEMA, \"topics\":[\"test\"], \"brokers\":[\"broker1\"], \"namespace\": \"mainspark\", \"output_topic\":\"outputtest\", \"project\":\"$PROJECT_NAME\", \"registry\":\"us-central1-docker.pkg.dev\", \"version\": 1, \"cassandra_cluster_name\": \"cluster1\"}"


* curl [ipaddress from ingress]:8000
* curl [ipaddress from ingress]:8000/database/create  -X POST 
* export AVRO_SCHEMA='{"name": "testapp", "type":"record", "doc": "testavro", "fields":[{"name": "first_name", "type":"string"}, {"name":"last_name", "type":"string"}]}'

* curl [ipaddress from ingress]:8000/database/table/update  -X POST -d "{\"organization\": \"$ORGANIZATION_NAME\", \"avro_schema\":$AVRO_SCHEMA, \"primary_keys\":[\"last_name\"] }"

* curl [ipaddress from ingress]:8000/job/replay  -X POST -d "{\"organization\": \"$ORGANIZATION_NAME\", \"avro_schema\":$AVRO_SCHEMA, \"topics\":[\"test\"], \"brokers\":[\"broker1\"], \"namespace\": \"mainspark\", \"output_topic\":\"outputtest\", \"project\":\"$PROJECT_NAME\", \"registry\":\"us-central1-docker.pkg.dev\", \"version\": 1, \"cassandra_cluster_name\": \"cluster1\"}"




## Knative: put on hold, for now...just use normal deploy/pod for now

Initial KNative app will be stateless: simply take a json payload (including kafka secrets, and maybe cassandra secrets, though kafka will be outside the cluster and cassandra is within cluster) and create the required applications.  There will be one spark streaming application per topic (to persist) and one spark streaming application for doing stateful transformations on the kafka topics.   

* sudo curl -L "https://storage.googleapis.com/knative-nightly/client/latest/kn-linux-amd64" -o /usr/local/bin/kn

* sudo chmod +x /usr/local/bin/kn

* kubectl apply --filename https://github.com/knative/serving/releases/download/v0.20.0/serving-crds.yaml

* kubectl apply --filename https://github.com/knative/serving/releases/download/v0.20.0/serving-core.yaml

* kubectl apply -f https://github.com/knative/net-kourier/releases/download/v0.19.1/kourier.yaml

* export EXTERNAL_IP=$(kubectl -n kourier-system get service kourier -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

* kubectl patch configmap/config-network --namespace knative-serving --type merge --patch '{"data":{"ingress.class":"kourier.ingress.networking.knative.dev"}}'

* export KNATIVE_DOMAIN="$EXTERNAL_IP.nip.io"

* kubectl patch configmap -n knative-serving config-domain -p "{"data": {"$KNATIVE_DOMAIN": ""}}"

* kubectl apply --filename back-end-app.yml

* kubectl get ksvc helloworld-go

Curl the URL to test


# dev area
* sudo docker build . -t spsbt -f ./test_container/Dockerfile
* sudo docker run -it spsbt /bin/bash
* spark-submit --master local[*] --class dhstest.FileSourceWrapper target/scala-2.12/kafka_and_file_connect.jar myapp ./tmp_file 0 Append /tmp
* sudo docker exec -it $(sudo -S docker ps -q  --filter ancestor=spsbt) /bin/bash
* echo {\"id\": 1,\"first_name\": \"John\", \"last_name\": \"Lindt\",  \"email\": \"jlindt@gmail.com\",\"gender\": \"Male\",\"ip_address\": \"1.2.3.4\"} >> ./tmp_file/mytest.json


# prometheus

* helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
* helm repo update
* kubectl create namespace monitoring
* helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring
* helm show values prometheus-community/kube-prometheus-stack
* kubectl port-forward svc/prometheus-operated 9090:9090
* kubectl apply -f prometheustest/prometheus.yml
* kubectl apply -f prometheustest/servicemonitor.yml
* kubectl apply -f prometheustest/service.yml
* kubectl apply -f prometheustest/pysparkjob.yml
* kubectl get pods -l sparkoperator.k8s.io/app-name=devfromfile

# python based

* pip3 install 'streamstate[test]'
* python3 setup.py test