const k8s = require('@kubernetes/client-node')

const getCoreClient = () => {
    const kc = getKubeConfig() //this may call loadFromCluster if on a cluster...but test this assumption
    return kc.makeApiClient(k8s.CoreV1Api)
}
const getKubeConfig = () => {
    const kc = new k8s.KubeConfig()
    //kc.loadFromCluster()
    kc.loadFromDefault()
    return kc
}
//const client = k8s.KubernetesObjectApi.makeApiClient(kc)
const getBetaClientClient = () => { //this may not be needed
    const kc = new k8s.KubeConfig()
    //kc.loadFromCluster()
    kc.loadFromDefault()
    return kc.makeApiClient(k8s.BatchV1beta1Api)
}

const createNamespace = (namespaceName) => {
    const client = getCoreClient()
    const namespace = {
        metadata: {
            name: namespaceName,
        },
    }
    client.createNamespace(namespace).then(
        (response) => {
            console.log('Created namespace');
            console.log(response);
            client.readNamespace(namespace.metadata.name).then((response) => {
                console.log(response);
            });
        },
        (err) => {
            //then namespace already exists
            console.log('Error!: ' + err);
        },
    );
}

const deleteNamespace = (namespaceName) => {
    const client = getClient()
    client.deleteNamespace(namespaceName).then(console.log).catch(console.error)
}

module.exports = {
    createNamespace,
    deleteNamespace,
    getCoreClient,
    getKubeConfig
}
