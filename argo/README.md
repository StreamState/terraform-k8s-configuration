
* kubectl create namespace argocd
* kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
* kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'


* kubectl create namespace argo
* kubectl apply -n argo -f https://raw.githubusercontent.com/argoproj/argo-workflows/stable/manifests/quick-start-postgres.yaml
* kubectl create clusterrolebinding daniel-cluster-admin-binding --clusterrole=cluster-admin --user=danstahl1138@gmail.com
* kubectl -n argo port-forward deployment/argo-server 2746:2746

* curl -sLO https://github.com/argoproj/argo/releases/download/v3.0.0-rc8/argo-linux-amd64.gz

* gunzip argo-linux-amd64.gz

* chmod +x argo-linux-amd64

* sudo mv ./argo-linux-amd64 /usr/local/bin/argo

* argo submit -n argo --watch https://raw.githubusercontent.com/argoproj/argo-workflows/master/examples/hello-world.yaml