from typing import List
from kubernetes.client import V1Role, V1ServiceAccount, V1RoleBinding
import os
import json

MAIN_APPLICATION_FILE = "local:///opt/spark/work-dir"


def spark_persist_job_spec(
    default_body: dict,
    image: str,
    brokers: List[str],
    topic: str,
    group_id: str,
    processing_interval: str,
    namespace: str,
    project: str,
    organization: str,
) -> dict:
    app_name = f"{topic}-persist"
    default_body["metadata"] = {
        "name": app_name,
        "namespace": namespace,
    }
    bucket = f"streamstate-sparkstorage-{organization}"
    history_bucket = f"streamstate-historyserver-{organization}"
    default_body["spec"]["hadoopConf"]["fs.gs.project.id"] = project
    default_body["spec"]["hadoopConf"]["fs.gs.system.bucket"] = bucket
    default_body["spec"]["sparkConf"]["spark.eventLog.dir"] = f"gs://{history_bucket}/"
    default_body["spec"]["image"] = image  # todo, we may be able to hardcode this
    # default_body["spec"]["mainClass"] = "PersistKafkaSourceWrapper"
    default_body["spec"]["mainApplicationFile"] = os.path.join(
        MAIN_APPLICATION_FILE, "persist_app.py"
    )

    output_struct = {
        "mode": "append",
        "checkpoint_location": "/tmp/checkpoint",
        "output_name": "",  # doesn't matter
        "processing_time": processing_interval,
    }

    kafka_struct = {"brokers": ",".join(brokers)}
    input_struct = {"topic": topic, "schema": {"fields": []}}  # doesnt matter
    default_body["spec"]["arguments"] = [
        app_name,
        json.dumps(output_struct),
        json.dumps(kafka_struct),
        json.dumps(input_struct),
    ]
    return default_body


## TODO, add kafka output
def spark_replay_file_spec(
    default_body: dict,
    image: str,
    brokers: List[str],
    folders_to_watch: List[str],  # probably the same name as kafka topics
    output_topic: str,
    group_id: str,
    max_file_age: str,
    namespace: str,
    project: str,
    organization: str,
    cassandra_table_name: str,
    cassandra_cluster_name: str,
) -> dict:
    name = "replay" + "-".join(folders_to_watch)
    default_body["metadata"] = {
        "name": name,
        "namespace": namespace,
    }
    bucket = f"streamstate-sparkstorage-{organization}"
    history_bucket = f"streamstate-historyserver-{organization}"
    default_body["spec"]["hadoopConf"]["fs.gs.project.id"] = project
    default_body["spec"]["hadoopConf"]["fs.gs.system.bucket"] = bucket
    default_body["spec"]["sparkConf"]["spark.eventLog.dir"] = f"gs://{history_bucket}/"
    default_body["spec"]["image"] = image
    default_body["spec"]["mainClass"] = "sparkwrappers.ReplayHistoryFromFile"
    default_body["spec"]["arguments"] = [
        name,
        # ",".join(brokers),
        # group_id,
        # output_topic,
        ",".join(f"gs://{bucket}/{folder}/" for folder in folders_to_watch),
        max_file_age,
        "/tmp/checkpoint",
        cassandra_table_name,
        cassandra_cluster_name,
    ]
    return default_body


def spark_state_job_spec(
    default_body: dict,
    image: str,
    brokers: List[str],
    topics: List[str],
    output_topic: str,
    group_id: str,
    namespace: str,
    project: str,
    organization: str,
    cassandra_table_name: str,
    cassandra_cluster_name: str,
) -> dict:
    name = "-".join(topics)
    default_body["metadata"] = {"name": f"{name}-application", "namespace": namespace}
    bucket = f"streamstate-sparkstorage-{organization}"
    history_bucket = f"streamstate-historyserver-{organization}"
    default_body["spec"]["hadoopConf"]["fs.gs.project.id"] = project
    default_body["spec"]["hadoopConf"]["fs.gs.system.bucket"] = bucket
    default_body["spec"]["sparkConf"]["spark.eventLog.dir"] = f"gs://{history_bucket}/"
    default_body["spec"]["image"] = image
    default_body["spec"]["mainClass"] = "sparkwrappers.KafkaSourceWrapper"
    default_body["spec"]["arguments"] = [
        f"{name}-application",
        ",".join(brokers),
        output_topic,
        group_id,
        ",".join(topics),
        "/tmp/checkpoint",
        cassandra_table_name,
        cassandra_cluster_name,
    ]
    return default_body