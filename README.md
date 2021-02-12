# getting started

* sudo snap install microk8s --classic
* sudo usermod -a -G microk8s $USER
* sudo chown -f -R $USER ~/.kube
* su - ${USER}
* microk8s status --wait-ready
* microk8s enable dashboard dns registry istio helm3
* microk8s kubectl get all --all-namespaces

# install flink operator

* microk8s helm3 repo add flink-operator-repo https://googlecloudplatform.github.io/flink-on-k8s-operator/
* microk8s helm3 install tstflink flink-operator-repo/flink-operator --set operatorImage.name=gcr.io/flink-operator/flink-operator:latest

* microk8s helm3 install tstflink flink-operator-repo/flink-operator --set operatorImage.name=mytest1

# diagnostics
* microk8s kubectl get crds | grep flinkclusters.flinkoperator.k8s.io
* microk8s kubectl get pods -n flink-operator-system

# play around with flink
* git clone git@github.com:GoogleCloudPlatform/flink-on-k8s-operator.git
* update ./flink-on-k8s-operator/helm-chart/flink-operator/update_template.sh to use `microk8s kubectl`
* cd ./flink-on-k8s-operator/helm-chart/flink-operator
* ./update_template.sh 
* microk8s helm3 install tstflink . --set operatorImage.name=gcr.io/flink-operator/flink-operator:latest

* microk8s kubectl apply -f ./flink-on-k8s-operator/config/samples/flinkoperator_v1beta1_flinksessioncluster.yaml



microk8s helm3 install tstflink . --set operatorImage.name=gcr.io/flink-operator/flink-operator:latest,flinkOperatorNamespace.name=flink-operator-system,flinkOperatorNamespace.create=false

microk8s helm3 delete tstflink