from pyspark.sql import SparkSession, DataFrame
import pyspark.sql.functions as F
from typing import List, Dict, Tuple, Callable
import sys

from utils import map_avro_to_spark_schema


def process(dfs: List[DataFrame]) -> DataFrame:
    return dfs[0].select("first_name", "last_name")


def kafka_wrapper(
    app_name: str,
    brokers: List[str],
    process: Callable[[List[DataFrame]], DataFrame],
    inputs: List[Tuple[str, dict]],
) -> DataFrame:
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    broker_str = ",".join(brokers)
    dfs = [
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", broker_str)
        .option("subscribe", topic)
        .load()
        .selectExpr("CAST(value AS STRING) as json")
        .select(F.from_json(F.col("json"), schema=schema["fields"]).alias("data"))
        .select("data.*")
        for (topic, schema) in inputs
    ]
    return process(dfs)


def file_wrapper(
    app_name: str,
    max_file_age: str,
    process: Callable[[List[DataFrame]], DataFrame],
    inputs: List[Tuple[str, dict]],
) -> DataFrame:
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    dfs = [
        spark.readStream.schema(schema["fields"])
        .option("maxFileAge", max_file_age)
        .json(location)
        for (location, schema) in inputs
    ]
    return process(dfs)


def write_kafka(batch_df: DataFrame, brokers: str, output_topic: str):
    batch_df.write.format("kafka").option("kafka.bootstrap.servers", brokers).option(
        "topic", output_topic
    ).save()


def write_cassandra(
    batch_df: DataFrame,
    cassandra_key_space: str,
    cassandra_table_name: str,
    cassandra_cluster_name: str,
):
    batch_df.write.format("org.apache.spark.sql.cassandra").option(
        "keyspace", cassandra_key_space
    ).option("table", cassandra_table_name).option(
        "cluster", cassandra_cluster_name
    ).mode(
        "APPEND"
    ).save()


def write_console(
    result: DataFrame,
    checkpoint: str,
    mode: str,
):
    result.writeStream.format("console").outputMode("append").option(
        "truncate", "false"
    ).option("checkpointLocation", checkpoint).start().awaitTermination()


def _write_df(df: DataFrame, write_fn: Callable[[DataFrame], None]):
    df.persist()
    write_fn(df)


def write_wrapper(
    result: DataFrame, checkpoint: str, mode: str, write_fn: Callable[[DataFrame], None]
):
    result.writeStream.outputMode(mode).option("truncate", "false").option(
        "checkpointLocation", checkpoint
    ).foreachBatch(lambda df, id: _write_df(df, write_fn)).start().awaitTermination()
