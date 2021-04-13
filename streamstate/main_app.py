from pyspark.sql import SparkSession, DataFrame
from typing import List, Dict, Tuple
import sys
from streamstate.utils import map_avro_to_spark_schema, convert_cassandra_dict
from streamstate.generic_wrapper import (
    file_wrapper,
    write_console,
    kafka_wrapper,
    write_wrapper,
    set_cassandra,
    write_cassandra,
    write_kafka,
)
from streamstate.process import Process
import json
import os
from streamstate.structs import OutputStruct, FileStruct, CassandraStruct, KafkaStruct


def kafka_source_wrapper(
    app_name: str,
    schema: List[Tuple[str, dict]],
    output: OutputStruct,
    files: FileStruct,
    cassandra: CassandraStruct,
    kafka: KafkaStruct,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    set_cassandra(cassandra, spark)
    df = kafka_wrapper(app_name, kafka.brokers, Process.process, schema, spark)

    def dual_write(batch_df: DataFrame):
        batch_df.persist()
        write_kafka(batch_df, kafka, output)
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
    cassandra_info = CassandraStruct.Schema().load(
        convert_cassandra_dict(
            raw_cassandra, os.getenv("username", ""), os.getenv("password", "")
        )
    )
    kafka_info = KafkaStruct.Schema().load(json.loads(kafka_struct))
    kafka_source_wrapper(
        app_name, json.loads(schema), output_info, file_info, cassandra_info, kafka_info
    )
