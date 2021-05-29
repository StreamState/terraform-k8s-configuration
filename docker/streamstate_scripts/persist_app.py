from pyspark.sql import SparkSession
import sys
import os
from streamstate_utils.generic_wrapper import (
    kafka_wrapper,
    write_wrapper,
    write_parquet,
)
import json
from streamstate_utils.structs import OutputStruct, KafkaStruct, InputStruct
import marshmallow_dataclass


def persist_topic(
    app_name: str,
    bucket: str,
    input: InputStruct,
    kafka: KafkaStruct,
    output: OutputStruct,
    checkpoint_location: str
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    df = kafka_wrapper(app_name, kafka.brokers, lambda dfs: dfs[0], [input], spark)
    write_wrapper(
        df,
        output,
        os.path.join(bucket, checkpoint_location),
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

    output_schema = marshmallow_dataclass.class_schema(OutputStruct)()
    output_info = output_schema.load(json.loads(output_struct))
    kafka_schema = marshmallow_dataclass.class_schema(KafkaStruct)()
    kafka_info = kafka_schema.load(json.loads(kafka_struct))
    input_schema = marshmallow_dataclass.class_schema(InputStruct)()
    input_info = input_schema.load(json.loads(input_struct))
    persist_topic(
        app_name,
        bucket,
        input_info,
        kafka_info,
        output_info,
        checkpoint_location
    )
