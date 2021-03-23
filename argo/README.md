
* kubectl create namespace argocd
* kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
* kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

# argo workflows

* kubectl create namespace argo-events
* kubectl apply -n argo-events -f https://raw.githubusercontent.com/argoproj/argo-workflows/stable/manifests/quick-start-postgres.yaml
* kubectl create clusterrolebinding daniel-cluster-admin-binding --clusterrole=cluster-admin --user=danstahl1138@gmail.com
* kubectl -n argo-events port-forward deployment/argo-server 2746:2746

* curl -sLO https://github.com/argoproj/argo/releases/download/v3.0.0-rc8/argo-linux-amd64.gz

* gunzip argo-linux-amd64.gz

* chmod +x argo-linux-amd64

* sudo mv ./argo-linux-amd64 /usr/local/bin/argo

* argo submit -n argo --watch https://raw.githubusercontent.com/argoproj/argo-workflows/master/examples/hello-world.yaml


# argo events
* kubectl apply -n argo-events -f https://raw.githubusercontent.com/argoproj/argo-events/stable/manifests/install.yaml
* kubectl apply -n argo-events -f https://raw.githubusercontent.com/argoproj/argo-events/stable/examples/eventbus/native.yaml

* kubectl -n argo-events apply -f argo/workflow.yml


# docker

* sudo docker build . -f ./argo/Dockerfile -t us.gcr.io/$PROJECT_NAME/scalacompile -t us.gcr.io/$PROJECT_NAME/scalacompile:v0.1.0
* sudo docker push us.gcr.io/$PROJECT_NAME/scalacompile:v0.1.0

* sudo docker build . -f ./argo/DockerInDocker.Dockerfile -t us.gcr.io/$PROJECT_NAME/dockerindocker -t us.gcr.io/$PROJECT_NAME/dockerindocker:v0.1.0
* sudo docker push us.gcr.io/$PROJECT_NAME/dockerindocker:v0.1.0

* sudo docker build . -f ./argo/Spark.Dockerfile -t us.gcr.io/$PROJECT_NAME/sparkbase -t us.gcr.io/$PROJECT_NAME/sparkbase:v0.1.0 
* sudo docker push us.gcr.io/$PROJECT_NAME/sparkbase:v0.1.0

# deploy workflow

* kubectl -n argo-events port-forward $(kubectl -n argo-events get pod -l eventsource-name=webhook -o name) 12000:12000 
* curl -X POST -d "{\"code\":\"$(base64 -w 0 ./src/main/scala/custom.scala)\"}" http://localhost:12000/example