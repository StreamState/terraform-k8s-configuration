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
    for (topic in topics) {

    }

    const brokersString = brokers.join(",")
}