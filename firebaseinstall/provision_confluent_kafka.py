from confluent_kafka.admin import AdminClient, NewTopic
from streamstate_utils.structs import KafkaStruct
from streamstate_utils.kafka_utils import (
    get_confluent_config,
    get_kafka_output_topic_from_app_name,
)
import sys
import json

REPLICATION_FACTOR = 3


def create_topics(admin_client, app_name: str, firestore_version: str):
    # this is async
    fs = admin_client.create_topics(
        [
            NewTopic(
                get_kafka_output_topic_from_app_name(app_name, firestore_version),
                REPLICATION_FACTOR,
            )
        ]
    )
    # wait till all are finished in parallel
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Topic {} created".format(topic))
        except Exception as e:
            print("Failed to create topic {}: {}".format(topic, e))


def main():
    _, app_name, kafka_struct, firestore_version = sys.argv
    kafka_info = KafkaStruct(**json.loads(kafka_struct))
    admin_client = AdminClient(
        get_confluent_config(
            kafka_info.brokers,
            api_key=kafka_info.confluent_api_key,
            secret=kafka_info.confluent_secret,
        )
    )
    create_topics(admin_client, app_name, firestore_version)


if __name__ == "__main__":
    main()
