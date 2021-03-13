import yaml
from kubernetes import client, config
from kubernetes.client.api import CustomObjectsApi
from create_body import spark_state_job_spec, spark_persist_job_spec
from kubernetes.client.api_client import ApiClient


def yaml_load(path: str) -> dict:
    with open(path) as file:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        spec = yaml.load(file, Loader=yaml.FullLoader)

        return spec


files = [
    "../sparkstreaming/spark-streaming-file-persist-template.yaml",
    "../sparkstreaming/spark-streaming-job-template.yaml",
]


def create_job(api: CustomObjectsApi, pay_load: dict):
    topics = pay_load["topics"]
    brokers = pay_load["brokers"]
    namespace = pay_load["namespace"]
    cassandraIp = pay_load["cassandraIp"]
    cassandraPassword = pay_load["cassandraPassword"]
    [file_persist, spark_job] = [yaml_load(ymlFile) for ymlFile in files]
    config.load_incluster_config()
    for topic in topics:
        file_persist_local = file_persist.copy()
        file_persist_local = spark_persist_job_spec(
            file_persist_local,
            "streamstate:latest",
            brokers,
            topic,
            namespace,
        )
        # this can throw, so make sure that we catch that when calling this function
        api_response = api.create_namespaced_custom_object(
            body=file_persist_local,
            namespace=namespace,
            group="sparkoperator.k8s.io",
            version="v1beta2",
            plural="sparkapplications",
        )
        print(api_response)
    name = "-".join(topics)
    spark_job = spark_state_job_spec(
        spark_job,
        "streamstate:latest",
        brokers,
        topics,
        namespace,
        cassandraIp,
        cassandraPassword,
    )
    print(spark_job)
    # this can throw, so make sure that we catch that when calling this function
    api_response = api.create_namespaced_custom_object(
        body=spark_job,
        namespace=namespace,
        group="sparkoperator.k8s.io",
        version="v1beta2",
        plural="sparkapplications",
    )
    print(api_response)


if __name__ == "__main__":
    config.load_incluster_config()
    apiclient = ApiClient()
    api = client.CustomObjectsApi(apiclient)
    create_job(
        api,
        {
            "topics": ["topic1"],
            "authType": "",
            "brokers": ["broker1"],
            "credentials": "",
            "namespace": "mynamespace",
            "cassandraIp": "127.0.0.1",
            "cassandraPassword": "hello",
        },
    )
