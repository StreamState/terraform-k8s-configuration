import yaml
from kubernetes import client, config


def yamlLoad(path: str) -> dict:
    with open(path) as file:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        spec = yaml.load(file, Loader=yaml.FullLoader)

        return spec


files = [
    "../sparkstreaming/spark-streaming-file-persist-template.yaml",
    "../sparkstreaming/spark-streaming-job-template.yaml",
]


def useJson(payLoad: dict):
    topics = payLoad["topics"]
    brokers = payLoad["brokers"]
    namespace = payLoad["namespace"]
    cassandraIp = payLoad["cassandraIp"]
    cassandraPassword = payLoad["cassandraPassword"]
    [file_persist, spark_job] = [yamlLoad(ymlFile) for ymlFile in files]
    config.load_incluster_config()
    api = client.CustomObjectsApi()

    for topic in topics:
        file_persist_local = file_persist.copy()
        file_persist_local["metadata"] = {
            "name": f"{topic}-persist",
            "namespace": namespace,
        }
        file_persist_local["spec"]["image"] = "streamstate:latest"
        file_persist_local["spec"]["arguments"] = [
            f"{topic}-persist",
            ",".join(brokers),
            "test-1",
            topic,
            "/tmp/sink",
            "/tmp/checkpoint",
        ]
        try:
            api_response = api.create_namespaced_custom_object(
                body=file_persist_local,
                namespace=namespace,
                group="sparkoperator.k8s.io",
                version="v1beta2",
                plural="sparkapplications",
            )
        except:
            print(api_response)
        print(api_response)
    name = "-".join(topics)
    spark_job["metadata"] = {"name": f"{name}-application", "namespace": namespace}
    spark_job["spec"]["image"] = "streamstate:latest"
    spark_job["spec"]["arguments"] = [
        f"{name}-application",
        ",".join(brokers),
        "test-1",
        topic,
        "/tmp/sink",
        "/tmp/checkpoint",
        cassandraIp,
        cassandraPassword,
    ]
    print(spark_job)
    api_response = api.create_namespaced_custom_object(
        body=spark_job,
        namespace=namespace,
        group="sparkoperator.k8s.io",
        version="v1beta2",
        plural="sparkapplications",
    )
    print(api_response)


if __name__ == "__main__":
    useJson(
        {
            "topics": ["topic1"],
            "authType": "",
            "brokers": ["broker1"],
            "credentials": "",
            "namespace": "mynamespace",
            "cassandraIp": "127.0.0.1",
            "cassandraPassword": "hello",
        }
    )
