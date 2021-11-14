
# helpful commands for teraform
* terraform state rm 'module.kubernetes-config'
* kubectl --kubeconfig terraform/organization/kubeconfig -n argo-events get pods

# install gcloud and kubectl for gcloud

* https://cloud.google.com/kubernetes-engine/docs/quickstart#standard
* gcloud components install kubectl

See https://cloud.google.com/community/tutorials/managing-gcp-projects-with-terraform

First time:
* export PROJECT_NAME=streamstatetest
* gcloud projects create ${PROJECT_NAME}  --set-as-default
* export TF_CREDS=~/.config/gcloud/${USER}-terraform-admin.json
* gcloud iam service-accounts keys create ${TF_CREDS} --iam-account terraform@${PROJECT_NAME}.iam.gserviceaccount.com
* export BILLING_ACCOUNT=$(cat account_id) # this needs to be created, found via `gcloud alpha billing accounts list`
* gcloud iam service-accounts create terraform --display-name "Terraform admin account"
* gcloud beta billing projects link $PROJECT_NAME --billing-account=$BILLING_ACCOUNT
* gcloud projects add-iam-policy-binding ${PROJECT_NAME} --member serviceAccount:terraform@${PROJECT_NAME}.iam.gserviceaccount.com --role roles/owner
* cd terraform/organization
* terraform init

Every time:

* cd terraform/organization
* export PROJECT_NAME=streamstatetest
* export ORGANIZATION_NAME=testorg
* export TF_CREDS=~/.config/gcloud/${USER}-terraform-admin.json
* export GOOGLE_APPLICATION_CREDENTIALS=${TF_CREDS}
* terraform apply -var-file="testing.tfvars"
* (direct connection with kubectl): gcloud container clusters get-credentials streamstatecluster-testorg --region=us-central1
* (connection through terraform kubeconfig): kubectl --kubeconfig terraform/organization/kubeconfig [etc]

To shut down:

* terraform destroy -var-file="testing.tfvars"

If anything hangs, you can delete the kubernetes module:

* terraform state rm 'module.kubernetes-config'

Make sure to delete any Compute Engine storage!!

# deploy workflow

First, an admin needs to create a new application with client id and secret in your oauth provider (eg Okta).  Then, use the client id and secret to make a post request to get a token.

For Okta:

* Base64 encode the client id and secret `BASE_64AUTH=$(echo -n clientID:clientsecret | base64 -w 0)`

* Request a token (assuming you have created a custom scope called "testemail", see https://developer.okta.com/docs/guides/customize-authz-server/create-scopes/) `TOKEN=$(curl --request POST \
  --url https://dev-20490044.okta.com/oauth2/default/v1/token \
  --header 'accept: application/json' \
  --header "authorization: Basic $BASE_64AUTH" \
  --header 'cache-control: no-cache' \
  --header 'content-type: application/x-www-form-urlencoded' \
  --data 'grant_type=client_credentials&scope=testemail' \
| python -c "import sys,json; print json.load(sys.stdin)['access_token']")`

* Finally, use the token to create a request to deploy `curl  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -X POST -d "{\"pythoncode\":\"$(base64 -w 0 examples/process.py)\", \"inputs\": $(cat examples/sampleinputs.json), \"assertions\": $(cat examples/assertedoutputs.json), \"kafka\": {\"brokers\": \"[yourbrokers]\", \"confluent_api_key\": \"[yourapikey]\", \"confluent_secret\": \"[yoursecret]\"}, \"outputs\": {\"mode\": \"append\", \"processing_time\":\"2 seconds\"}, \"table\":{\"primary_keys\":[\"field1\"], \"output_schema\":[{\"name\":\"field1\", \"type\": \"string\"}]}, \"appname\":\"mytestapp\"}" https://testorg.streamstate.org/api/deploy -k`

* To replay: 
`curl  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -X POST -d "{\"inputs\": $(cat examples/sampleinputs.json), \"kafka\": {\"brokers\": \"broker1,broker2\"}, \"outputs\": {\"mode\": \"append\", \"processing_time\":\"2 seconds\"}, \"fileinfo\":{\"max_file_age\": \"2d\"}, \"table\":{\"primary_keys\":[\"field1\"], \"output_schema\":[{\"name\":\"field1\", \"type\": \"string\"}]}, \"appname\":\"mytestapp\", \"code_version\": 1}" https://testorg.streamstate.org/api/replay -k`

* To stop: `curl  -H "Authorization: Bearer $TOKEN" -X POST https://testorg.streamstate.org/api/mytestapp/stop -k `

* List active applications: `curl  -H "Authorization: Bearer $TOKEN" -X GET https://testorg.streamstate.org/api/applications -k `


# upload json to bucket

* kubectl apply -f gke/replay_from_file.yml
* echo {\"id\": 1,\"first_name\": \"John\", \"last_name\": \"Lindt\",  \"email\": \"jlindt@gmail.com\",\"gender\": \"Male\",\"ip_address\": \"1.2.3.4\"} >> ./mytest.json


You may have to create a subfolder first (eg, /test)

* gsutil cp ./mytest.json gs://streamstate-sparkstorage-testorg/mytestapp/topic1

* echo {\"field1\": \"somevalue\"} > ./mytest1.json
* gsutil cp ./mytest1.json gs://streamstate-sparkstorage-testorg/mytestapp/topic1

Read from the result firebase:


curl  -H "Authorization: Bearer 7b1d331a-e67f-4ee8-b1f8-930320f18039" -X GET https://testorg.streamstate.org/api/mytestapp/features/1?filter="somevalue" -k 



# prometheus

Grafana password:
* kubectl get secret --namespace serviceplane-testorg grafana -o jsonpath="{.data.admin-password}" | base64 --decode

# test workload identity

kubectl run -it \
--image google/cloud-sdk:slim \
--serviceaccount cert-manager \
--namespace serviceplane-testorg \
workload-identity-test




gcloud projects get-iam-policy streamstatetest  \
--flatten="bindings[].members" \
--format='table(bindings.role)' \
--filter="bindings.members:dns-testorg@streamstatetest.iam.gserviceaccount.com"
