const k8s = require('@kubernetes/client-node');

const kc = new k8s.KubeConfig()
kc.loadFromDefault()
const k8sApi = kc.makeApiClient(k8s.CoreV1Api)

const fastify = require('fastify')
fastify.register(require('fastify-static'), {
    root: path.join(__dirname, 'public'),
    prefix: '/public/', // optional: default '/'
})
const app = fastify()

app.post('/user', async (req, reply) => {
    const result = createNewSecret()
    return {
        error: false,
        username: req.body.username
    };
});

app.listen(3000).then(() => {
    console.log('Server running at http://localhost:3000/');
});

const createNewSecret = async () => {

    const namespace = "systemplane-testorg" //get from env variable
    const metadata = { name: "mysecret", namespace }
    const data = { 'key': 'hello' }
    const api_version = 'v1'
    const kind = 'secret'
    const body = new k8s.V1Secret(api_version, data, kind, metadata)
    const deleteSecret = k8sApi.deleteNamespacedSecret(metadata.name, namespace)
    return k8sApi.createNamespacedSecret(namespace, body)
}

const server = restify.createServer();
server.get('/hi', createNewSecret);
//server.head('/hello/:name', respond);

server.listen(8080, () => {
    console.log('%s listening at %s', server.name, server.url);
})
server.get(/\/docs\/public\/?.*/, restify.plugins.serveStatic({
    directory: './public'
}));

/*

const namespace = "systemplane-testorg" //get from env variable
const metadata = { name: "mysecret", namespace }
const data = { 'key': 'hello' }
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

api_response = v1.create_namespaced_secret(namespace, body)*/