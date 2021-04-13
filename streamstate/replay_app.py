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
from streamstate.structs import OutputStruct, FileStruct, CassandraStruct, KafkaStruct

from streamstate.process import Process
import json
import os


def replay_from_file(
    app_name: str,
    schema: List[Tuple[str, dict]],
    output: OutputStruct,
    files: FileStruct,
    cassandra: CassandraStruct,
    kafka: KafkaStruct,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    set_cassandra(cassandra, spark)
    df = file_wrapper(app_name, files.max_file_age, Process.process, schema, spark)

    def dual_write(batch_df: DataFrame):
        batch_df.persist()
        # todo, uncomment this
        # write_kafka(batch_df, kafka, output)
        write_cassandra(batch_df, cassandra)

    write_wrapper(df, output, dual_write)


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
        output_struct,
        file_struct,
        cassandra_struct,
        kafka_struct,
        schema,
    ] = sys.argv

    output_info = OutputStruct.Schema().load(json.loads(output_struct))
    file_info = FileStruct.Schema().load(json.loads(file_struct))
    raw_cassandra = json.loads(cassandra_struct)
    [cassandra_key_space, cassandra_table_name] = raw_cassandra[
        "cassandra_table"
    ].split(".")
    raw_cassandra["cassandra_key_space"] = cassandra_key_space
    raw_cassandra["cassandra_table_name"] = cassandra_table_name
    raw_cassandra["cassandra_user"] = os.getenv("password", "")
    raw_cassandra["cassandra_password"] = os.getenv("username", "")
    cassandra_info = CassandraStruct.Schema().load(raw_cassandra)
    kafka_info = KafkaStruct.Schema().load(json.loads(kafka_struct))
    # cassandra_ip = os.getenv("CASSANDRA_LOADBALANCER_SERVICE_HOST", "")
    # cassandra_port = os.getenv("CASSANDRA_LOADBALANCER_SERVICE_PORT", "")

    replay_from_file(
        app_name, json.loads(schema), output_info, file_info, cassandra_info, kafka_info
    )
