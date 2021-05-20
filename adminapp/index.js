const k8s = require('@kubernetes/client-node');

const kc = new k8s.KubeConfig()
kc.loadFromDefault()

const k8sApi = kc.makeApiClient(k8s.CoreV1Api)

const namespace = "systemplane-testorg" //get from env variable
const metadata = { name: "mysecret", namespace }
const data = {}
const api_version = 'v1'
const kind = 'secret'
const body = new k8s.V1Secret(api_version, data, kind, metadata)
k8sApi.createNamespacedSecret(namespace, body)

//need to create/reset existing secrets
v1 = client.CoreV1Api()
namespace = 'kube-system'
metadata = { 'name': 'pk-test-tls', 'namespace': 'kube-system' }
data = { 'tls.crt': '###BASE64 encoded crt###', 'tls.key': '###BASE64 encoded Key###' }
api_version = 'v1'
kind = 'none'
body = kubernetes.client.V1Secret(api_version, data, kind, metadata,
    type = 'kubernetes.io/tls')

api_response = v1.create_namespaced_secret(namespace, body)