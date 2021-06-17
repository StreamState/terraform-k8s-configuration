from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import sys
import os
from streamstate_utils.generic_wrapper import (
    kafka_wrapper,
    write_wrapper,
    write_parquet,
)
import json
from streamstate_utils.structs import OutputStruct, KafkaStruct, InputStruct


def persist_topic(
    app_name: str,
    bucket: str,
    input: InputStruct,
    kafka: KafkaStruct,
    output: OutputStruct,
    checkpoint_location: str,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    df = kafka_wrapper(
        kafka.brokers,
        lambda dfs: dfs[0],
        [input],
        spark,
    )
    write_wrapper(
        df,
        output,
        os.path.join(bucket, checkpoint_location, app_name),
        lambda df: write_parquet(df, app_name, bucket, input.topic),
    )


# examples
# mode = "append"
# schema_struct =
#     {"topic": "topic1",
#         "schema": {
#             "fields": [
#                 {"name": "first_name", "type": "string"},
#                 {"name": "last_name", "type": "string"},
#             ]
#         },
#     }
#
if __name__ == "__main__":
    [
        _,
        app_name,
        bucket,  # bucket name including gs://
        output_struct,
        kafka_struct,
        input_struct,
        checkpoint_location,
    ] = sys.argv

    output_info = OutputStruct(**json.loads(output_struct))
    kafka_info = KafkaStruct(**json.loads(kafka_struct))
    input_info = InputStruct(**json.loads(input_struct))
    persist_topic(
        app_name, bucket, input_info, kafka_info, output_info, checkpoint_location
    )
