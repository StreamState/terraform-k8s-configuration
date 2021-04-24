from pyspark.sql import SparkSession, DataFrame
from typing import List, Dict, Tuple
import sys
from streamstate_utils.pyspark_utils import map_avro_to_spark_schema
from streamstate_utils.generic_wrapper import (
    file_wrapper,
    write_console,
)
from process import process
import json
from streamstate_utils.structs import OutputStruct, FileStruct, InputStruct
import marshmallow_dataclass


def dev_from_file(
    app_name: str,
    max_file_age: str,
    bucket: str,
    inputs: List[InputStruct],
    checkpoint: str,
    mode: str,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    df = file_wrapper(app_name, max_file_age, bucket, process, inputs, spark)
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
        _,
        app_name,  # could this come from output schema's name?  eg, [outputschema.name]-dev-app?
        bucket,  # bucket name including gs://
        output_struct,
        file_struct,
        input_struct,
    ] = sys.argv
    output_schema = marshmallow_dataclass.class_schema(OutputStruct)()
    output_info = output_schema.load(json.loads(output_struct))
    file_schema = marshmallow_dataclass.class_schema(FileStruct)()
    file_info = file_schema.load(json.loads(file_struct))
    input_schema = marshmallow_dataclass.class_schema(InputStruct)()
    input_info = [input_schema.load(v) for v in json.loads(input_struct)]
    dev_from_file(
        app_name,
        file_info.max_file_age,
        bucket,
        input_info,
        output_info.checkpoint_location,
        output_info.mode,
    )
