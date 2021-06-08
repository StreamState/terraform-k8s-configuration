from pyspark.sql import SparkSession, DataFrame
from typing import List
import sys
from streamstate_utils.firestore import get_firestore_inputs_from_config_map
from streamstate_utils.generic_wrapper import (
    kafka_wrapper,
    write_wrapper,
    write_firestore,
    write_kafka,
)

from process import process
import json
import os
from streamstate_utils.structs import (
    OutputStruct,
    KafkaStruct,
    InputStruct,
    FirestoreOutputStruct,
    TableStruct,
)


def kafka_source_wrapper(
    app_name: str,
    bucket: str,
    input: List[InputStruct],
    output: OutputStruct,
    firestore: FirestoreOutputStruct,
    table: TableStruct,
    kafka: KafkaStruct,
    checkpoint_location: str,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    df = kafka_wrapper(app_name, kafka.brokers, process, input, spark)

    def dual_write(batch_df: DataFrame):
        batch_df.persist()
        write_kafka(batch_df, kafka, app_name, firestore.version)
        write_firestore(batch_df, firestore, table)

    write_wrapper(
        df, output, os.path.join(bucket, checkpoint_location, app_name), dual_write
    )


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
        _,
        app_name,
        bucket,  # bucket name including gs://
        table_struct,
        output_struct,
        kafka_struct,
        input_struct,
        checkpoint_location,
        version,  ## todo, is this the best way? (probably)
    ] = sys.argv
    # table_schema = marshmallow_dataclass.class_schema(TableStruct)()
    # output_schema = marshmallow_dataclass.class_schema(OutputStruct)()
    output_info = OutputStruct(**json.loads(output_struct))
    kafka_info = KafkaStruct(**json.loads(kafka_struct))
    firestore = get_firestore_inputs_from_config_map(app_name, version)
    # input_schema = marshmallow_dataclass.class_schema(InputStruct)()
    table_info = TableStruct(**json.loads(table_struct))
    input_info = [InputStruct(**v) for v in json.loads(input_struct)]

    kafka_source_wrapper(
        app_name,
        bucket,
        input_info,
        output_info,
        firestore,
        table_info,
        kafka_info,
        checkpoint_location,
    )
