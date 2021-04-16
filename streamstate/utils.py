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
from typing import List, Dict, Tuple, Callable, NamedTuple
from pyspark.sql import DataFrame
import os


def get_folder_location(app_name: str, topic: str) -> str:
    return os.path.join(app_name, topic)


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


def convert_cassandra_dict(
    raw_cassandra: dict, cassandra_user: str, cassandra_password: str
) -> dict:
    [cassandra_key_space, cassandra_table_name] = raw_cassandra[
        "cassandra_table"
    ].split(".")
    raw_cassandra["cassandra_key_space"] = cassandra_key_space
    raw_cassandra["cassandra_table_name"] = cassandra_table_name
    raw_cassandra["cassandra_user"] = cassandra_user
    raw_cassandra["cassandra_password"] = cassandra_password
    return raw_cassandra
