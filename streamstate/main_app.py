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

## how to add this at real time??
from streamstate.process import process
import json
import os
from streamstate.structs import (
    OutputStruct,
    FileStruct,
    CassandraStruct,
    KafkaStruct,
    InputStruct,
)
import marshmallow_dataclass


def kafka_source_wrapper(
    app_name: str,
    input: List[InputStruct],
    output: OutputStruct,
    files: FileStruct,
    cassandra: CassandraStruct,
    kafka: KafkaStruct,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    set_cassandra(cassandra, spark)
    df = kafka_wrapper(app_name, kafka.brokers, process, input, spark)

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
        input_struct,
    ] = sys.argv
    output_schema = marshmallow_dataclass.class_schema(OutputStruct)()
    output_info = output_schema.load(json.loads(output_struct))
    file_schema = marshmallow_dataclass.class_schema(FileStruct)()
    file_info = file_schema.load(json.loads(file_struct))
    raw_cassandra = json.loads(cassandra_struct)
    cassandra_schema = marshmallow_dataclass.class_schema(CassandraStruct)()
    cassandra_info = cassandra_schema.load(
        convert_cassandra_dict(
            raw_cassandra, os.getenv("username", ""), os.getenv("password", "")
        )
    )
    kafka_info = marshmallow_dataclass.class_schema(KafkaStruct)().load(
        json.loads(kafka_struct)
    )

    input_schema = marshmallow_dataclass.class_schema(InputStruct)()

    input_info = [input_schema.load(v) for v in json.loads(input_struct)]

    kafka_source_wrapper(
        app_name, input_info, output_info, file_info, cassandra_info, kafka_info
    )
