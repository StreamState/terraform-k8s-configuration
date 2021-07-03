const base64 = require('base-64')
const { v4: uuidv4 } = require('uuid')
const fs = require('fs')

const createNewSecret = (secretName, secretText, k8s, k8sApi, namespace, keyName = 'token') => {
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
const generateNewSecret = (secretName, k8s, k8sApi, namespace) => {
    const secretText = uuidv4()
    return createNewSecret(secretName, secretText, k8s, k8sApi, namespace)
}

const getWriteToken=()=>{
    return new Promise((res, rej)=>fs.readFile("/etc/secret-volume/write_token/token", (e, d)=>{
        return e?rej(e):res(d)
    }))
}
module.exports={
    getWriteToken,
    generateNewSecret,
    createNewSecret,
}