const k8s = require('@kubernetes/client-node');

const kc = new k8s.KubeConfig()
kc.loadFromDefault()
const k8sApi = kc.makeApiClient(k8s.CoreV1Api)

const k8sApiCustomObject = kc.makeApiClient(k8s.CustomObjectsApi)
const { v4: uuidv4 } = require('uuid')
const fastify = require('fastify')()
const base64 = require('base-64')
const path = require('path')
fastify.register(require('fastify-static'), {
    root: path.join(__dirname, 'public'),
    prefix: '/public/', // optional: default '/'
})
fastify.register(require('fastify-formbody'))
const {
    WRITE_TOKEN_NAME: writeTokenName,
    READ_TOKEN_NAME: readTokenName,
    CONFLUENT_KEY_NAME: confluentKeyName,
    CONFLUENT_SECRET_NAME: confluentSecretName,
    NAMESPACE: namespace
} = process.env

fastify.post('/rotate/write', (req, reply) => {
    generateNewSecret(writeTokenName)
        .then(secret => reply.send({ secret }))
        .catch(e => {
            console.log(e)
            reply.send({ error: e.message })
        })
})
fastify.post('/rotate/read', (req, reply) => {
    generateNewSecret(readTokenName)
        .then(secret => reply.send({ secret }))
        .catch(e => {
            console.log(e)
            reply.send({ error: e.message })
        })
})
fastify.post('/confluent/create', (req, reply) => {
    return Promise.all([
        createNewSecret(confluentKeyName, req.body.confluentKey, 'key'),
        createNewSecret(confluentSecretName, req.body.confluentSecret, 'secret')
    ]).then(_ => reply.send({ success: true }))
        .catch(e => {
            console.log(e)
            reply.send({ error: e.message })
        })
})


fastify.listen(process.env.PORT, '0.0.0.0').then((address) => {
    console.log(`Server running at ${address}`);
})
fastify.get('/', (req, reply) => {
    return reply.sendFile('hello.html') // serving path.join(__dirname, 'public', 'myHtml.html') directly
})
const convertListByGroup=listOfSparkApps=>{
    console.log(listOfSparkApps)
    return Object.entries(listOfSparkApps.reduce((agg, val)=>{
        const sparkApp=agg[val.metadata.name]||[]
        return {
            ...agg, 
            [val.metadata.name]:[
                ...sparkApp,
                val
                //val
            ]
        }
    }, {

    })).map(([key, value])=>({
        sparkApp: key, 
        value
    }))
}
const getSparkApplications=()=>{
    //k8sApiCustomObject.getNamespacedCustomObject
    k8sApiCustomObject.listNamespacedCustomObjects(
        "sparkoperator.k8s.io",
        "v1beta2",
        namespace,
        "sparkapplications",
        //labelSelector=`app=${app_name}`,
    ).then(response=>{
        return convertListByGroup(response)
    })
}
const createNewSecret = (secretName, secretText, keyName = 'token') => {
    const b64secret = base64.encode(secretText)
    const metadata = { name: secretName, namespace }
    const data = { [keyName]: b64secret }
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
const generateNewSecret = (secretName) => {
    const secretText = uuidv4()
    return createNewSecret(secretName, secretText)
}

module.exports={
    convertListByGroup
}