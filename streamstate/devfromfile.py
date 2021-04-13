from pyspark.sql import SparkSession, DataFrame
from typing import List, Dict, Tuple
import sys
from streamstate.utils import map_avro_to_spark_schema
from streamstate.generic_wrapper import (
    file_wrapper,
    write_console,
    kafka_wrapper,
    write_wrapper,
    set_cassandra,
    write_cassandra,
    write_kafka,
    write_parquet,
)


def process(dfs: List[DataFrame]) -> DataFrame:
    return dfs[0].select("first_name", "last_name")


def dev_from_file(
    app_name: str,
    max_file_age: str,
    checkpoint: str,
    inputs: List[Tuple[str, dict]],
    mode: str,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    df = file_wrapper(app_name, max_file_age, process, inputs, spark)
    write_console(df, checkpoint, mode)


def kafka_source_wrapper(
    app_name: str,
    brokers: List[str],
    output_topic: str,
    inputs: List[Tuple[str, dict]],
    checkpoint: str,
    mode: str,
    cassandra_ip: str,  # TODO, consider wrapping these in an object/class/struct
    cassandra_port: str,
    cassandra_user: str,
    cassandra_password: str,
    cassandra_key_space: str,
    cassandra_table_name: str,
    cassandra_cluster_name: str,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    set_cassandra(
        cassandra_ip, cassandra_port, cassandra_user, cassandra_password, spark
    )
    broker_str = ",".join(brokers)
    df = kafka_wrapper(app_name, broker_str, process, inputs, spark)

    def dual_write(batch_df: DataFrame):
        batch_df.persist()
        write_kafka(batch_df, broker_str, output_topic)
        write_cassandra(
            batch_df, cassandra_key_space, cassandra_table_name, cassandra_cluster_name
        )

    write_wrapper(df, checkpoint, mode, dual_write)


def persist_topic(
    app_name: str,
    brokers: List[str],
    output_folder: str,
    input: Tuple[str, dict],
    checkpoint: str,
    mode: str,
):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    broker_str = ",".join(brokers)
    df = kafka_wrapper(app_name, broker_str, lambda dfs: dfs[0], [input], spark)
    write_wrapper(df, checkpoint, mode, lambda df: write_parquet(df, output_folder))


if __name__ == "__main__":
    [app_name, file_location, max_file_age, checkpoint] = sys.argv
    fields = [
        {"name": "first_name", "type": "string"},
        {"name": "last_name", "type": "string"},
    ]
    inputs = [(file_location, {"fields": fields})]
    dev_from_file(app_name, max_file_age, checkpoint, inputs)
