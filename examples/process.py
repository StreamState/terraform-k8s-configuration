from typing import List
from pyspark.sql import DataFrame


def process(dfs: List[DataFrame]) -> DataFrame:
    return dfs[0]
