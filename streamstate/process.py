# this file will get overwritten
from pyspark.sql import DataFrame
from typing import List

# from sparkstreaming.utils import ProcessBaseClass


def process(dfs: List[DataFrame]) -> DataFrame:
    return dfs[0].select("field1")