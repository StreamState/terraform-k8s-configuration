from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
    BooleanType,
    LongType,
    DoubleType,
    FloatType,
    DataType,
)
from typing import List, Dict
import sys


def _convert_type(avro_type: str) -> DataType:
    avro_type_conversion = {
        "boolean": BooleanType(),
        "int": IntegerType(),
        "long": LongType(),
        "float": FloatType(),
        "double": DoubleType(),
        "string": StringType(),
    }
    return avro_type_conversion[avro_type]


def map_avro_to_spark_schema(fields: List[Dict[str, str]]) -> StructType:
    return StructType(
        [
            StructField(field["name"], _convert_type(field["type"]), True)
            for field in fields
        ]
    )


def process(dfs: List[DataFrame]) -> DataFrame:
    return dfs[0].select("first_name", "last_name")


def dev_from_file(
    app_name: str,
    file_locations: str,
    max_file_age: str,
    checkpoint: str,
    fields: List[Dict[str, str]],  # todo...need schema per file source
):
    files = file_locations.split(",")
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    schema = map_avro_to_spark_schema(fields)
    dfs = [
        spark.readStream.schema(schema).option("maxFileAge", max_file_age).json(fl)
        for fl in files
    ]
    result = process(dfs)
    result.writeStream.format("console").outputMode("append").option(
        "truncate", "false"
    ).option("checkpointLocation", checkpoint).start().awaitTermination()


if __name__ == "__main__":
    [app_name, file_locations, max_file_age, checkpoint] = sys.argv
    fields = [
        {"name": "first_name", "type": "string"},
        {"name": "last_name", "type": "string"},
    ]
    dev_from_file(app_name, file_locations, max_file_age, checkpoint, fields)