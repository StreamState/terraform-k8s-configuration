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
const {
    WRITE_TOKEN_NAME: writeTokenName,
    READ_TOKEN_NAME: readTokenName,
    NAMESPACE: namespace
} = process.env

fastify.post('/rotate/write', (req, reply) => {
    createNewSecret(writeTokenName)
        .then(secret => reply.send({ secret }))
        .catch(e => {
            console.log(e)
            reply.send({ error: e.message })
        })
})
fastify.post('/rotate/read', (req, reply) => {
    createNewSecret(readTokenName)
        .then(secret => reply.send({ secret }))
        .catch(e => {
            console.log(e)
            reply.send({ error: e.message })
        })
})
/*
fastify.get('/rotate', (req, reply) => {
    return reply.send({ hello: "world" })
})*/

fastify.listen(process.env.PORT, '0.0.0.0').then((address) => {
    console.log(`Server running at ${address}`);
})
fastify.get('/', (req, reply) => {
    return reply.sendFile('hello.html') // serving path.join(__dirname, 'public', 'myHtml.html') directly
})
const createNewSecret = (secretName) => {
    const secretText = uuidv4()
    const b64secret = base64.encode(secretText)
    const metadata = { name: secretName, namespace }
    const data = { 'token': b64secret }
    let secret = new k8s.V1Secret()
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