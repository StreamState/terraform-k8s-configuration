# argo workflows

* kubectl create namespace argo-events
* kubectl apply -n argo-events -f https://raw.githubusercontent.com/argoproj/argo-workflows/stable/manifests/namespace-install.yaml
* kubectl patch svc argo-server -n argo-events -p '{"spec": {"type": "LoadBalancer"}}' #todo!  auth!
* kubectl get svc argo-server -n argo-events
* kubectl create clusterrolebinding daniel-cluster-admin-binding --clusterrole=cluster-admin --user=danstahl1138@gmail.com # is this needed in gke?
* kubectl -n argo-events port-forward deployment/argo-server 2746:2746

* curl -sLO https://github.com/argoproj/argo/releases/download/v3.0.0-rc8/argo-linux-amd64.gz

* gunzip argo-linux-amd64.gz

* chmod +x argo-linux-amd64

* sudo mv ./argo-linux-amd64 /usr/local/bin/argo


# argo events
* kubectl apply -n argo-events -f https://raw.githubusercontent.com/argoproj/argo-events/stable/manifests/namespace-install.yaml
* kubectl apply -n argo-events -f argo/eventbus.yml

TODO!!! Add security to this endpoint and expose it via load balancer rather than through portforward
* kubectl apply -n argo-events -f argo/eventsource.yml
* kubectl -n argo-events apply -f argo/workflow.yml


# docker

* sudo docker build . -f ./argo/scalacompile.Dockerfile -t us.gcr.io/$PROJECT_NAME/scalacompile -t us.gcr.io/$PROJECT_NAME/scalacompile:v0.5.0
* sudo docker push us.gcr.io/$PROJECT_NAME/scalacompile:v0.5.0

* sudo docker build . -f ./argo/dockerindocker.Dockerfile -t us.gcr.io/$PROJECT_NAME/dockerindocker -t us.gcr.io/$PROJECT_NAME/dockerindocker:v0.5.0
* sudo docker push us.gcr.io/$PROJECT_NAME/dockerindocker:v0.5.0

* sudo docker build . -f ./argo/sparkbase.Dockerfile -t us.gcr.io/$PROJECT_NAME/sparkbase -t us.gcr.io/$PROJECT_NAME/sparkbase:v0.1.0 
* sudo docker push us.gcr.io/$PROJECT_NAME/sparkbase:v0.1.0

# deploy workflow

* kubectl -n argo-events port-forward $(kubectl -n argo-events get pod -l eventsource-name=webhook -o name) 12000:12000 
* curl -X POST -d "{\"code\":\"$(base64 -w 0 ./src/main/scala/custom.scala)\"}" http://localhost:12000/example