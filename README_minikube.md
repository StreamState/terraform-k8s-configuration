# getting started

* minikube start
* minikube start --kubernetes-version=v1.17.11

# install flink operator

* helm repo add flink-operator-repo https://googlecloudplatform.github.io/flink-on-k8s-operator/
* #helm install tstflink flink-operator-repo/flink-operator --set operatorImage.name=gcr.io/flink-operator/flink-operator:latest

* wget https://github.com/GoogleCloudPlatform/flink-on-k8s-operator/archive/flink-operator-0.1.1.zip
* unzip flink-operator-0.1.1.zip && cd flink-on-k8s-operator-flink-operator-0.1.1/
* helm install  tstflink ./helm-chart/flink-operator/ --set operatorImage.name=gcr.io/flink-operator/flink-operator:latest

* git clone git@github.com:GoogleCloudPlatform/flink-on-k8s-operator.git
* cd flink-on-k8s-operator
* make deploy 


# diagnostics

* kubectl get crds | grep flinkclusters.flinkoperator.k8s.io
* kubectl get pods -n flink-operator-system