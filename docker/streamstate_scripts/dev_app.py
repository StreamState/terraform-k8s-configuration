from pyspark.sql import SparkSession
from typing import List
import sys
from streamstate_utils.generic_wrapper import (
    file_wrapper,
    write_console,
)
import os
from process import process
import json
from streamstate_utils.structs import OutputStruct, FileStruct, InputStruct


def dev_from_file(
    app_name: str,
    max_file_age: str,
    bucket: str,
    inputs: List[InputStruct],
    checkpoint_location: str,
    mode: str,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    df = file_wrapper(app_name, max_file_age, bucket, process, inputs, spark)
    write_console(df, os.path.join(bucket, checkpoint_location), mode)


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
        app_name,  #
        bucket,  # bucket name including gs://
        output_struct,
        file_struct,
        input_struct,
        checkpoint_location,
    ] = sys.argv
    output_info = OutputStruct(**json.loads(output_struct))
    file_info = FileStruct(**json.loads(file_struct))
    input_info = [InputStruct(**v) for v in json.loads(input_struct)]
    dev_from_file(
        app_name,
        file_info.max_file_age,
        bucket,
        input_info,
        checkpoint_location,
        output_info.mode,
    )
