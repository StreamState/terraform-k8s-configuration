from pyspark.sql import SparkSession, DataFrame
from typing import List, Dict, Tuple
import sys
from streamstate_utils.utils import (
    map_avro_to_spark_schema,
    get_cassandra_inputs_from_config_map,
    get_cassandra_outputs_from_config_map,
)
from streamstate_utils.generic_wrapper import (
    file_wrapper,
    write_console,
    kafka_wrapper,
    write_wrapper,
    set_cassandra,
    write_cassandra,
    write_kafka,
)

## how to add this at real time??
from process import process
import json
import os
from streamstate_utils.structs import (
    OutputStruct,
    FileStruct,
    CassandraInputStruct,
    CassandraOutputStruct,
    KafkaStruct,
    InputStruct,
)
import marshmallow_dataclass


def kafka_source_wrapper(
    app_name: str,
    input: List[InputStruct],
    output: OutputStruct,
    files: FileStruct,
    cassandra_input: CassandraInputStruct,
    cassandra_output: CassandraOutputStruct,
    kafka: KafkaStruct,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    set_cassandra(cassandra_input, spark)
    df = kafka_wrapper(app_name, kafka.brokers, process, input, spark)

    def dual_write(batch_df: DataFrame):
        batch_df.persist()
        write_kafka(batch_df, kafka, output)
        write_cassandra(batch_df, cassandra_output)

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
        kafka_struct,
        input_struct,
        version,  ## todo, is this the best way? (probably)
    ] = sys.argv
    output_schema = marshmallow_dataclass.class_schema(OutputStruct)()
    output_info = output_schema.load(json.loads(output_struct))
    file_schema = marshmallow_dataclass.class_schema(FileStruct)()
    file_info = file_schema.load(json.loads(file_struct))
    cassandra_input = get_cassandra_inputs_from_config_map()
    cassandra_output = get_cassandra_outputs_from_config_map(app_name, version)
    kafka_info = marshmallow_dataclass.class_schema(KafkaStruct)().load(
        json.loads(kafka_struct)
    )

    input_schema = marshmallow_dataclass.class_schema(InputStruct)()

    input_info = [input_schema.load(v) for v in json.loads(input_struct)]

    kafka_source_wrapper(
        app_name,
        input_info,
        output_info,
        file_info,
        cassandra_input,
        cassandra_output,
        kafka_info,
    )
