from pyspark.sql import SparkSession, DataFrame
from typing import List, Dict, Tuple
import sys
from streamstate.utils import map_avro_to_spark_schema
from streamstate.generic_wrapper import (
    file_wrapper,
    write_console,
    kafka_wrapper,
    write_wrapper,
    set_cassandra,
    write_cassandra,
    write_kafka,
    write_parquet,
)
from streamstate.process import Process
import json
import os


def kafka_source_wrapper(
    app_name: str,
    brokers: str,
    output_topic: str,
    inputs: List[Tuple[str, dict]],
    checkpoint: str,
    mode: str,
    cassandra_ip: str,  # TODO, consider wrapping these in an object/class/struct
    cassandra_port: str,
    cassandra_user: str,
    cassandra_password: str,
    cassandra_key_space: str,
    cassandra_table_name: str,
    cassandra_cluster_name: str,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    set_cassandra(
        cassandra_ip, cassandra_port, cassandra_user, cassandra_password, spark
    )
    df = kafka_wrapper(app_name, brokers, Process.process, inputs, spark)

    def dual_write(batch_df: DataFrame):
        batch_df.persist()
        write_kafka(batch_df, brokers, output_topic)
        write_cassandra(
            batch_df, cassandra_key_space, cassandra_table_name, cassandra_cluster_name
        )

    write_wrapper(df, checkpoint, mode, dual_write)


# examples
# mode = "append"
# schema = [
#     (
#         "topic1",
#         {
#             "fields": [
#                 {"name": "first_name", "type": "string"},
#                 {"name": "last_name", "type": "string"},
#             ]
#         },
#     )
# ]
if __name__ == "__main__":
    [
        app_name,
        brokers,
        output_topic,
        checkpoint,
        mode,
        schema,
        cassandra_table,
        cassandra_cluster,
    ] = sys.argv
    cassandra_password = os.getenv("password", "")
    cassandra_user = os.getenv("username", "")
    cassandra_ip = os.getenv("CASSANDRA_LOADBALANCER_SERVICE_HOST", "")
    cassandra_port = os.getenv("CASSANDRA_LOADBALANCER_SERVICE_PORT", "")
    [cassandra_key_space, cassandra_table_name] = cassandra_table.split(".")
    kafka_source_wrapper(
        app_name,
        brokers,
        output_topic,
        json.loads(schema),
        checkpoint,
        mode,
        cassandra_ip,
        cassandra_port,
        cassandra_user,
        cassandra_password,
        cassandra_key_space,
        cassandra_table_name,
        cassandra_cluster,
    )
