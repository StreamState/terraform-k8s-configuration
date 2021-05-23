const k8s = require('@kubernetes/client-node');

const kc = new k8s.KubeConfig()
kc.loadFromDefault()
const k8sApi = kc.makeApiClient(k8s.CoreV1Api)
const { v4: uuidv4 } = require('uuid')
const fastify = require('fastify')()
const base64 = require('base-64')
const path = require('path')
fastify.register(require('fastify-static'), {
    root: path.join(__dirname, 'public'),
    prefix: '/public/', // optional: default '/'
})

fastify.post('/rotate', (req, reply) => {
    createNewSecret()
        .then(secret => reply.send({ secret }))
        .catch(e => {
            console.log(e)
            reply.send({ error: e.message })
        })
})

fastify.get('/rotate', (req, reply) => {
    return reply.send({ hello: "world" })
})

fastify.listen(process.env.PORT, '0.0.0.0').then((address) => {
    console.log(`Server running at ${address}`);
})
fastify.get('/', (req, reply) => {
    return reply.sendFile('hello.html') // serving path.join(__dirname, 'public', 'myHtml.html') directly
})
const createNewSecret = () => {
    const secretText = uuidv4()
    const b64secret = base64.encode(secretText)
    const namespace = process.env.NAMESPACE // "systemplane-testorg" //get from env variable
    const metadata = { name: "streamstate-webhook-token", namespace }
    const data = { 'token': b64secret }
    let secret = new k8s.V1Secret() //(api_version, data, kind, metadata)
    secret.kind = "Secret"
    secret.apiVersion = 'v1'
    secret.metadata = metadata
    secret.data = data
    return k8sApi.deleteNamespacedSecret(metadata.name, namespace)
        .catch(e => console.log(e.message))
        .then(() => {
            return k8sApi.createNamespacedSecret(namespace, secret)
        })
        .then(() => secretText)
}