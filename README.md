
# helpful commands for teraform
* terraform state rm 'module.kubernetes-config'
* kubectl --kubeconfig terraform/organization/kubeconfig -n argo-events get pods

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

# Cassandra

https://docs.datastax.com/en/cass-operator/doc/cass-operator/cassOperatorConnectWithinK8sCluster.html

* kubectl get secrets/cassandra-secret -n mainspark --template={{.data.password}} | base64 -d
* kubectl --kubeconfig terraform/organization/kubeconfig exec -n mainspark -i -t -c cassandra cluster1-dc1-default-sts-0 -- /opt/cassandra/bin/cqlsh -u cluster1-superuser -p $(kubectl --kubeconfig terraform/organization/kubeconfig get secrets/cassandra-secret -n mainspark --template={{.data.password}} | base64 -d)
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
* cat $TF_CREDS | sudo docker login -u _json_key --password-stdin https://gcr.io
* sudo docker build . -f ./argo/scalacompile.Dockerfile -t gcr.io/$PROJECT_NAME/scalacompile -t gcr.io/$PROJECT_NAME/scalacompile:v0.5.0
* sudo docker push gcr.io/$PROJECT_NAME/scalacompile:v0.5.0

* sudo docker build . -f ./argo/sparkbase.Dockerfile -t gcr.io/$PROJECT_NAME/sparkbase -t gcr.io/$PROJECT_NAME/sparkbase:v0.1.0 
* sudo docker push gcr.io/$PROJECT_NAME/sparkbase:v0.1.0

# argo helps

To find webui url:
* kubectl --kubeconfig terraform/organization/kubeconfig -n argo-events get svc
* go to [webuiurl]:2746 in your favorite browser

# deploy workflow

* kubectl -n argo-events port-forward $(kubectl -n argo-events get pod -l eventsource-name=webhook -o name) 12000:12000 
* curl -X POST -d "{\"code\":\"$(base64 -w 0 ./src/main/scala/custom.scala)\"}" http://localhost:12000/example


# upload json to bucket

* echo {\"id\": 1,\"first_name\": \"John\", \"last_name\": \"Lindt\",  \"email\": \"jlindt@gmail.com\",\"gender\": \"Male\",\"ip_address\": \"1.2.3.4\"} >> ./mytest.json
* gsutil cp ./mytest.json gs://streamstate-sparkstorage/
* kubectl logs examplegcp-driver
* kubectl port-forward examplegcp-driver 4040:4040 # to view spark-ui, go to localhost:4040


# python consume cassandra

* python3 -m venv env
* source env/bin/activate
* pip3 install -r ./pythonexample/requirements.txt
* python3 pythonexample/connect_cassandra.py

# Kubectl service 

This is needed for the back end app.  There are two choices here: leverage argo cd and its rest API to kick off "builds"/workflows or use a live knative app to convert json to deploy applications.  

For now, I am going to use a knative app.  In the future it is likely more maintainable to use Argo.

Needed functionality:
* Authentication and secrets storage, multi-tenant
* Deploy applications in unique namespaces for each tenant
* Host spark ui for jobs within a namespace
* RBAC for specific jobs

## Knative

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