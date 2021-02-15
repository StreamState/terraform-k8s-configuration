# getting started

* minikube start --cpus 4 --memory 6000 --kubernetes-version=v1.20.2
* minikube addons enable registry
* minikube addons enable dashboard
* #minikube addons enable istio
* eval $(minikube docker-env)

# install spark operator

* helm repo add spark-operator https://googlecloudplatform.github.io/spark-on-k8s-operator
* helm install my-release spark-operator/spark-operator --namespace spark-operator --create-namespace
* kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/spark-on-k8s-operator/master/manifest/spark-rbac.yaml

Find the local ip address
* minikube ssh
* ping host.minikube.internal

put this IP adress in [the spark config](./sparkstreaming/spark-streaming.yaml) for the broker:

arguments:
    - [the ip address]:19092
    - test-1
    - test.test

# Install confluent (kafka)

Install docker compose:
* sudo curl -L "https://github.com/docker/compose/releases/download/1.28.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
* sudo chmod +x /usr/local/bin/docker-compose

From https://docs.confluent.io/platform/current/quickstart/cos-docker-quickstart.html and https://www.confluent.io/blog/kafka-client-cannot-connect-to-broker-on-aws-on-docker-etc/

Edit [docker-compose](./kafka/docker-compose.yml): 

KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://broker:29092,PLAINTEXT_HOST://localhost:9092,RMOFF_DOCKER_HACK://[the ip address]:19092

* cd kafka
* sudo docker-compose up -d

Make sure its running
* sudo docker-compose ps
* sudo docker-compose exec broker kafka-topics \
  --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 1 \
  --topic test.test
* sudo docker-compose exec broker bash -c "seq 42 | kafka-console-producer --request-required-acks 1 --broker-list localhost:29092 --topic test.test && echo 'Produced 42 messages.'"

* cd ..

# examples

Create the jar:
* sbt assembly 

Compile the docker:
* docker build . -t dhs_test -f ./sparkstreaming/Dockerfile

Run
* kubectl apply -f ./sparkstreaming/spark-streaming.yaml
* kubectl get sparkapplications word-count -o=yaml
* kubectl describe sparkapplication word-count
* kubectl delete -f ./sparkstreaming/spark-streaming.yaml



# Knative

This is needed for our back-end app
* sudo curl -L "https://storage.googleapis.com/knative-nightly/client/latest/kn-linux-amd64" -o /usr/local/bin/kn
* sudo chmod +x /usr/local/bin/kn
* kubectl apply --filename https://github.com/knative/serving/releases/download/v0.20.0/serving-crds.yaml
* kubectl apply --filename https://github.com/knative/serving/releases/download/v0.20.0/serving-core.yaml


* kubectl apply -f https://github.com/knative/net-kourier/releases/download/v0.19.1/kourier.yaml
* export EXTERNAL_IP=$(kubectl -n kourier-system get service kourier -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
* kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress.class":"kourier.ingress.networking.knative.dev"}}'
* export KNATIVE_DOMAIN="$EXTERNAL_IP.nip.io"
* kubectl patch configmap -n knative-serving config-domain -p "{\"data\": {\"$KNATIVE_DOMAIN\": \"\"}}"
* kubectl apply --filename back-end-app.yml
* kubectl get ksvc helloworld-go

Curl the URL to test
