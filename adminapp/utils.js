const base64 = require('base-64')
const { v4: uuidv4 } = require('uuid')
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
const getSparkApplications=(k8sApiCustomObject)=>{
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
const createNewSecret = (secretName, secretText, k8s, k8sApi, keyName = 'token') => {
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
const generateNewSecret = (secretName, k8s, k8sApi) => {
    const secretText = uuidv4()
    return createNewSecret(secretName, secretText, k8s, k8sApi)
}

module.exports={
    convertListByGroup,
    generateNewSecret,
    createNewSecret,

}