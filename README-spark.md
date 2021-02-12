# getting started

* minikube start --cpus 4 --kubernetes-version=v1.20.2
* minikube addons enable registry
* eval $(minikube docker-env)

# install spark operator

* helm repo add spark-operator https://googlecloudplatform.github.io/spark-on-k8s-operator
* helm install my-release spark-operator/spark-operator --namespace spark-operator --create-namespace
* kubectl apply -f manifest/spark-rbac.yaml


# diagnostics

* kubectl get pods -n spark-operator


# examples

* docker build . -t dhs_test
* kubectl apply -f spark-streaming.yaml
* kubectl get sparkapplications word-count -o=yaml
* kubectl describe sparkapplication word-count
* kubectl delete -f spark-streaming.yaml

# write to kafka

* docker run -d \
   --net=host \
   --name=zk-1 \
   -e ZOOKEEPER_SERVER_ID=1 \
   -e ZOOKEEPER_CLIENT_PORT=22181 \
   -e ZOOKEEPER_TICK_TIME=2000 \
   -e ZOOKEEPER_INIT_LIMIT=5 \
   -e ZOOKEEPER_SYNC_LIMIT=2 \
   -e ZOOKEEPER_SERVERS="localhost:22888:23888" \
   confluentinc/cp-zookeeper:5.0.0

* docker run -d \
    --net=host \
    --name=kafka-1 \
    -e KAFKA_ZOOKEEPER_CONNECT=localhost:22181 \
    -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:29092 \
    confluentinc/cp-kafka:5.0.0

* docker run \
  --net=host \
  --rm \
  confluentinc/cp-kafka:5.0.0 \
  kafka-topics --create --topic bar --partitions 1 --replication-factor 1 --if-not-exists --zookeeper localhost:32181

* docker run \
    --net=host \
    --rm \
    confluentinc/cp-kafka:5.0.0 \
    kafka-topics --describe --topic bar --zookeeper localhost:32181

(different terminal)
* sudo docker run \
  --net=host \
  --rm confluentinc/cp-kafka:5.0.0 \
  kafka-console-producer --broker-list localhost:29092 --topic bar "hello world"