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
from streamstate.structs import OutputStruct, FileStruct


def dev_from_file(
    app_name: str,
    max_file_age: str,
    inputs: List[Tuple[str, dict]],
    checkpoint: str,
    mode: str,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    df = file_wrapper(app_name, max_file_age, Process.process, inputs, spark)
    write_console(df, checkpoint, mode)


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
        schema,
    ] = sys.argv
    output_info = OutputStruct.Schema().load(json.loads(output_struct))
    file_info = FileStruct.Schema().load(json.loads(file_struct))
    dev_from_file(
        app_name,
        file_info.max_file_age,
        json.loads(schema),
        output_info.checkpoint_location,
        output_info.mode,
    )
