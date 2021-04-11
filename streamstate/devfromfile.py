from pyspark.sql import SparkSession, DataFrame
from typing import List, Dict, Tuple
import sys
from utils import map_avro_to_spark_schema
from generic_wrapper import file_wrapper, write_console


def process(dfs: List[DataFrame]) -> DataFrame:
    return dfs[0].select("first_name", "last_name")


def dev_from_file(
    app_name: str,
    max_file_age: str,
    checkpoint: str,
    inputs: List[Tuple[str, dict]],
):
    df = file_wrapper(
        app_name,
        max_file_age,
        process,
    )
    write_console(df, checkpoint, "append")


if __name__ == "__main__":
    [app_name, file_location, max_file_age, checkpoint] = sys.argv
    fields = [
        {"name": "first_name", "type": "string"},
        {"name": "last_name", "type": "string"},
    ]
    inputs = [(file_location, {"fields": fields})]
    dev_from_file(app_name, max_file_age, checkpoint, inputs)
