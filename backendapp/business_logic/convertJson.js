const { apply } = require('./kubectlApply')
const fs = require('fs')
const yaml = require('js-yaml')
const { promisify } = require('util')
const { getCoreClient, getKubeConfig } = require('./createNamespace')
const useJson = (payLoad) => {
    //TODO!  need to figure out credentials, see 
    // https://stackoverflow.com/questions/60450182/kafka-spark-structured-streaming-with-sasl-ssl-authentication, 
    // https://docs.databricks.com/spark/latest/structured-streaming/kafka.html
    const {
        topics,
        authType, //for kafka
        brokers, //for kafka
        credentials, //for kafka, and maybe cassandra
        namespace,  //unique per tenant
        cassandraIp, //this should be provided by the SaaS app, not by the client/tenant.  However, I want the backendapp app to be stateless
        cassandraPassword //for now, use basic auth
    } = payLoad
    fsp = promisify(fs.readFile)
    const kc = getKubeConfig()
    Promise.all([
        fsp("../sparkstreaming/spark-streaming-file-persist-template.yaml", 'utf8').then(yaml.safeLoad),
        fsp("../sparkstreaming/spark-streaming-job-template.yaml", 'utf8').then(yaml.safeLoad),
    ]).then(([file_persist, spark_job]) => {
        for (topic in topics) {
            const yml = {
                ...file_persist,
                metadata: {
                    name: `${topic}-persist`,
                    namespace
                },
                spec: {
                    ...file_persist.spec,
                    image: 'streamstate:latest',
                    arguments: [
                        `${topic}-persist`,
                        brokers.join(','),
                        'test-1',
                        topic,
                        '/tmp/sink',
                        '/tmp/checkpoint'
                    ]
                }
            }
            //console.log(yml)
            apply(kc, yml).then(console.log).catch(() => console.log("errored"))
            //console.log(topicApp)
        }
        const yml = {
            ...spark_job,
            metadata: {
                name: `${topics.join("-")}-application`,
                namespace
            },
            spec: {
                ...spark_job.spec,
                image: 'streamstate:latest',
                arguments: [
                    `${topic}-persist`,
                    brokers.join(','),
                    'test-1',
                    topics.join(','),
                    '/tmp/sink',
                    '/tmp/checkpoint',
                    cassandraIp,
                    cassandraPassword
                ]
            }
        }
        //console.log(yml)
        apply(kc, yml).then(console.log).catch(() => console.log("errored"))
    })
}

module.exports = {
    useJson
}