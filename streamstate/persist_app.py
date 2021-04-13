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
from streamstate.structs import OutputStruct, KafkaStruct


def persist_topic(
    app_name: str,
    schema: Tuple[str, dict],
    kafka: KafkaStruct,
    output: OutputStruct,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    df = kafka_wrapper(app_name, kafka.brokers, lambda dfs: dfs[0], [schema], spark)
    write_wrapper(df, output, lambda df: write_parquet(df, output.output_name))


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
    [app_name, output_struct, kafka_struct, schema] = sys.argv
    output_info = OutputStruct.Schema().load(json.loads(output_struct))
    kafka_info = KafkaStruct.Schema().load(json.loads(kafka_struct))
    persist_topic(
        app_name,
        json.loads(schema),
        kafka_info,
        output_info,
    )
