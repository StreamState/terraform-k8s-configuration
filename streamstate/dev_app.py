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


def dev_from_file(
    app_name: str,
    max_file_age: str,
    checkpoint: str,
    inputs: List[Tuple[str, dict]],
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
    [app_name, max_file_age, checkpoint, mode, schema] = sys.argv
    ##    {"name": "first_name", "type": "string"},
    #    {"name": "last_name", "type": "string"},
    # ]
    # inputs = [(file_location, {"fields": fields})]
    dev_from_file(app_name, max_file_age, checkpoint, json.loads(schema), mode)