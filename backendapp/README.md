# Run

* sudo docker build . -f backendapp/Dockerfile -t us.gcr.io/$PROJECT_NAME/streamstaterest -t us.gcr.io/$PROJECT_NAME/streamstaterest:v0.1.0
* sudo docker push us.gcr.io/$PROJECT_NAME/streamstaterest
* kubectl apply -f backendapp/job.yml
* kubectl port-forward pod/$(kubectl get pods -l bb=web --output=jsonpath='{.items[*].metadata.name}') 30001:8000

* curl 127.0.0.1:30001

* curl 127.0.0.1:30001/new_tenant/ -X POST -d '{"name": "test1"}'

* curl 127.0.0.1:30001/new_job/ -X POST -d '{"topics":["topic1"], "brokers":["broker1"], "namespace":"test1", "cassandraIp":""}'

* curl 127.0.0.1:30001/new_database/ -X POST -d '{ "namespace":"default", "app_name": "testc"}'

# delete

* kubectl delete -f backendapp/job.yml