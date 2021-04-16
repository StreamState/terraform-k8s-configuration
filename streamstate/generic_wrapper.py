from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.streaming import StreamingQuery
import pyspark.sql.functions as F
from typing import List, Dict, Tuple, Callable
import sys
import shutil
from streamstate.utils import map_avro_to_spark_schema, get_folder_location
import json
from streamstate.structs import (
    OutputStruct,
    FileStruct,
    CassandraStruct,
    KafkaStruct,
    InputStruct,
)


def process(dfs: List[DataFrame]) -> DataFrame:
    return dfs[0].select("first_name", "last_name")


def kafka_wrapper(
    app_name: str,
    brokers: str,
    process: Callable[[List[DataFrame]], DataFrame],
    inputs: List[InputStruct],
    spark: SparkSession,
) -> DataFrame:
    dfs = [
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", brokers)
        .option("subscribe", input.topic)
        .load()
        .selectExpr("CAST(value AS STRING) as json")
        .select(
            F.from_json(
                F.col("json"), schema=map_avro_to_spark_schema(input.schema.fields)
            ).alias("data")
        )
        .select("data.*")
        for input in inputs
    ]
    return process(dfs)


def set_cassandra(
    cassandra: CassandraStruct,
    spark: SparkSession,
):
    spark.conf.set("spark.cassandra.connection.host", cassandra.cassandra_ip)
    spark.conf.set("spark.cassandra.connection.rpc.port", cassandra.cassandra_port)
    spark.conf.set("spark.cassandra.auth.username", cassandra.cassandra_user)
    spark.conf.set("spark.cassandra.auth.password", cassandra.cassandra_password)


def file_wrapper(
    app_name: str,
    max_file_age: str,
    process: Callable[[List[DataFrame]], DataFrame],
    inputs: List[InputStruct],
    spark: SparkSession,
) -> DataFrame:
    dfs = [
        spark.readStream.schema(map_avro_to_spark_schema(input.schema.fields))
        .option("maxFileAge", max_file_age)
        .json(get_folder_location(app_name, input.topic))
        for input in inputs
    ]
    return process(dfs)


def write_kafka(batch_df: DataFrame, kafka: KafkaStruct, output: OutputStruct):
    batch_df.write.format("kafka").option(
        "kafka.bootstrap.servers", kafka.brokers
    ).option("topic", output.output_name).save()


def write_parquet(batch_df: DataFrame, output_folder: str):
    batch_df.write.format("parquet").option("path", output_folder).save()


# make sure to call set_cassandra before this
def write_cassandra(batch_df: DataFrame, cassandra: CassandraStruct):
    batch_df.write.format("org.apache.spark.sql.cassandra").option(
        "keyspace", cassandra.cassandra_key_space
    ).option("table", cassandra.cassandra_table_name).option(
        "cluster", cassandra.cassandra_cluster
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


def write_wrapper(
    result: DataFrame,
    output: OutputStruct,
    write_fn: Callable[[DataFrame], None],
    # processing_time: str = "0",
):
    result.writeStream.outputMode(output.mode).option("truncate", "false").trigger(
        processingTime=output.processing_time
    ).option("checkpointLocation", output.checkpoint_location).foreachBatch(
        lambda df, id: write_fn(df)
    ).start().awaitTermination()
