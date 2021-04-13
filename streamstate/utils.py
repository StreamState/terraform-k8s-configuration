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


from abc import ABC, abstractmethod

##from collections import namedtuple

# MyStruct = namedtuple("Process", "field1 field2 field3")


# class Process(NamedTuple):
#    mode: str
#    schema: List[Tuple[str, dict]]  # topic/location and avro schema
#    process: Callable[[List[DataFrame]], DataFrame]


class ProcessBaseClass(ABC):
    mode: str
    schema: List[Tuple[str, dict]]  # topic/location and avro schema

    def __init__(
        self,
        mode: str,
        schema: List[Tuple[str, dict]],
    ):
        self.mode = mode
        self.schema = schema

    @staticmethod
    @abstractmethod
    def process(dfs: List[DataFrame]) -> DataFrame:
        pass
