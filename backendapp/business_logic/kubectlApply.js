const k8s = require('@kubernetes/client-node')
async function apply(kubeConfig, spec) {
    //const kc = new k8s.KubeConfig();
    //kc.loadFromDefault();
    //const client = k8s.KubernetesObjectApi.makeApiClient(kc);
    //const fsReadFileP = promisify(fs.readFile);
    //const specString = await fsReadFileP(specPath, 'utf8');
    //const specs = yaml.safeLoadAll(specString);
    //const validSpecs = specs.filter((s) => s && s.kind && s.metadata);

    // this is to convince the old version of TypeScript that metadata exists even though we already filtered specs
    // without metadata out
    const client = k8s.KubernetesObjectApi.makeApiClient(kubeConfig)
    spec.metadata = spec.metadata || {};
    spec.metadata.annotations = spec.metadata.annotations || {};
    delete spec.metadata.annotations['kubectl.kubernetes.io/last-applied-configuration'];
    spec.metadata.annotations['kubectl.kubernetes.io/last-applied-configuration'] = JSON.stringify(spec);
    try {
        // try to get the resource, if it does not exist an error will be thrown and we will end up in the catch
        // block.
        await client.read(spec);
        console.log("spec exists!")
        // we got the resource, so it exists, so patch it
        const response = await client.patch(spec);
        console.log("patched!")
        return response.body
    } catch (e) {
        console.log(e)
        // we did not get the resource, so it does not exist, so create it
        const response = await client.create(spec);
        console.log("spec created")
        return response.body
    }
}

module.exports = {
    apply
}