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


def persist_topic(
    app_name: str,
    brokers: str,
    output_folder: str,
    input: Tuple[str, dict],
    checkpoint: str,
    mode: str,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    df = kafka_wrapper(app_name, brokers, lambda dfs: dfs[0], [input], spark)
    write_wrapper(df, checkpoint, mode, lambda df: write_parquet(df, output_folder))


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
    [app_name, brokers, output_folder, checkpoint, mode, schema] = sys.argv
    persist_topic(
        app_name, brokers, output_folder, json.loads(schema), checkpoint, mode
    )
