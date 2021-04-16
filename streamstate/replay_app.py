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
from streamstate.structs import (
    OutputStruct,
    FileStruct,
    CassandraStruct,
    KafkaStruct,
    InputStruct,
)
import marshmallow_dataclass
from streamstate.process import process
import json
import os


def replay_from_file(
    app_name: str,
    inputs: List[InputStruct],
    output: OutputStruct,
    files: FileStruct,
    cassandra: CassandraStruct,
    kafka: KafkaStruct,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    set_cassandra(cassandra, spark)
    df = file_wrapper(app_name, files.max_file_age, process, inputs, spark)

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
    kafka_schema = marshmallow_dataclass.class_schema(KafkaStruct)()
    kafka_info = kafka_schema.load(json.loads(kafka_struct))
    # cassandra_ip = os.getenv("CASSANDRA_LOADBALANCER_SERVICE_HOST", "")
    # cassandra_port = os.getenv("CASSANDRA_LOADBALANCER_SERVICE_PORT", "")
    input_schema = marshmallow_dataclass.class_schema(InputStruct)()
    input_info = [input_schema.load(v) for v in json.loads(input_struct)]
    replay_from_file(
        app_name, input_info, output_info, file_info, cassandra_info, kafka_info
    )
