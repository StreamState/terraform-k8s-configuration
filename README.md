# getting started

* minikube start --cpus 8 --memory 8000 --kubernetes-version=v1.20.2
* minikube addons enable registry
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

* sudo docker-compose exec broker bash -c 'echo {\"id\": 1,\"first_name\": \"John\", \"last_name\": \"Lindt\",  \"email\": \"jlindt@gmail.com\",\"gender\": \"Male\",\"ip_address\": \"1.2.3.4\"} | kafka-console-producer --request-required-acks 1 --broker-list localhost:29092 --topic test.test && echo "Produced 1 message."'

* sudo docker-compose exec broker kafka-console-producer --request-required-acks 1 --broker-list localhost:29092 --topic test.test hello

* cd ..

# examples

Create the jar:
* sbt assembly 

Compile the docker:
* docker build . -t dhs_test -f ./sparkstreaming/Dockerfile

Run
* kubectl apply -f ./sparkstreaming/spark-streaming.yaml
* kubectl get pods
* kubectl logs kafka-wrapper-driver 
* kubectl delete -f ./sparkstreaming/spark-streaming.yaml

# dev area
* sudo docker build . -t spsbt -f ./test_container/Dockerfile
* sudo docker run -it spsbt /bin/bash
* spark-submit --master local[*] --class dhstest.FileSourceWrapper target/scala-2.12/kafka_and_file_connect.jar myapp ./tmp_file 0 Append /tmp
* sudo docker exec -it $(sudo -S docker ps -q  --filter ancestor=spsbt) /bin/bash
* echo {\"id\": 1,\"first_name\": \"John\", \"last_name\": \"Lindt\",  \"email\": \"jlindt@gmail.com\",\"gender\": \"Male\",\"ip_address\": \"1.2.3.4\"} >> ./tmp_file/mytest.json

# Cassandra

* helm repo add datastax https://datastax.github.io/charts
* helm repo update
* helm install cass-operator datastax/cass-operator  --namespace cass-operator --create-namespace

In real life/google cloud, configure a new storage, using eg `kubectl apply -f ./cassandra/storage.yaml`

* kubectl -n cass-operator apply -f ./cassandra/datacenter.yaml

Check progress

* kubectl get pods -n cass-operator -o wide
* kubectl -n cass-operator get cassdc/dc1 -o "jsonpath={.status.cassandraOperatorProgress}"

Start being able to query

https://docs.datastax.com/en/cass-operator/doc/cass-operator/cassOperatorConnectWithinK8sCluster.html

* kubectl get secrets/cluster1-superuser -n cass-operator --template={{.data.password}} | base64 -d
* kubectl exec -n cass-operator -i -t -c cassandra cluster1-dc1-default-sts-0 -- /opt/cassandra/bin/cqlsh -u cluster1-superuser -p $(kubectl get secrets/cluster1-superuser -n cass-operator --template={{.data.password}} | base64 -d)
* CREATE KEYSPACE IF NOT EXISTS cycling WITH replication = { 'class' : 'NetworkTopologyStrategy', 'dc1' : '1' };
* CREATE TABLE IF NOT EXISTS cycling.cyclist_semi_pro (
   first_name text, 
   last_name text, 
   PRIMARY KEY (last_name));
* INSERT INTO cycling.cyclist_semi_pro (first_name, last_name) VALUES ('Carlos', 'Perotti');


* kubectl get pod cluster1-dc1-default-sts-0 --template='{{(index (index .spec.containers 0).ports 0).containerPort}}{{"\n"}}' -n cass-operator
* kubectl port-forward pod/cluster1-dc1-default-sts-0 30500:9042 -n cass-operator




# python consume cassandra

* python3 -m venv env
* source env/bin/activate
* pip3 install -r ./pythonexample/requirements.txt
* python3 pythonexample/connect_cassandra.py
