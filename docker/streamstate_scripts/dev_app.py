from pyspark.sql import SparkSession
from typing import List
import sys
from streamstate_utils.generic_wrapper import (
    dev_file_wrapper,
    write_console,
)
import os
from process import process
import json
from streamstate_utils.structs import FileStruct, InputStruct
from streamstate_utils.utils import get_folder_location


def dev_from_file(
    app_name: str,
    max_file_age: str,
    inputs: List[InputStruct],
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    base_folder = "."
    for input in inputs:
        os.makedirs(
            os.path.join(base_folder, get_folder_location(app_name, input.topic))
        )
    df = dev_file_wrapper(app_name, max_file_age, base_folder, process, inputs, spark)
    write_console(df, "/tmp")


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
        file_struct,
        input_struct,
    ] = sys.argv
    file_info = FileStruct(**json.loads(file_struct))
    input_info = [InputStruct(**v) for v in json.loads(input_struct)]
    dev_from_file(
        app_name,
        file_info.max_file_age,
        input_info,
    )
