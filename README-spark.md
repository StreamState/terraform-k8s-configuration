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
* 



* sudo docker push $(minikube ip):5000/dhs_test

* kubectl apply -f spark-streaming.yaml
* kubectl get sparkapplications word-count -o=yaml
* kubectl describe sparkapplication word-count
* kubectl delete -f spark-streaming.yaml

