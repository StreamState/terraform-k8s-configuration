from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.streaming import StreamingQuery
import pyspark.sql.functions as F
from typing import List, Dict, Tuple, Callable
import sys
import shutil
from streamstate.utils import map_avro_to_spark_schema
import os
import json
from streamstate.structs import OutputStruct, FileStruct, CassandraStruct, KafkaStruct


def process(dfs: List[DataFrame]) -> DataFrame:
    return dfs[0].select("first_name", "last_name")


def helper_for_file(
    app_name: str,
    max_file_age: str,
    process: Callable[[List[DataFrame]], DataFrame],
    inputs: List[Tuple[str, List[dict], dict]],
    spark: SparkSession,
    expecteds: List[dict],
) -> StreamingQuery:
    """
    This will be used for unit testing developer code
    Major inputs:

    process is the logic for manipulating streaming dataframes
    inputs is a list of "topic" names, example records from topic, and schema for topic
    expecteds is a list of expected output
    """
    file_dir = app_name
    try:
        shutil.rmtree(file_dir)
        print("folder exists, deleting")
    except:
        print("folder doesn't exist, creating")
    try:
        os.mkdir(file_dir)
        for (folder, _, _) in inputs:
            os.mkdir(os.path.join(file_dir, folder))

        df = file_wrapper(
            app_name,
            max_file_age,
            process,
            [
                (os.path.join(file_dir, folder), schema)
                for (folder, _, schema) in inputs
            ],
            spark,
        )
        file_name = "localfile.json"

        for (folder, data, _) in inputs:
            file_path = os.path.join(file_dir, folder, file_name)
            with open(file_path, mode="w") as test_file:
                json.dump(data, test_file)

        q = (
            df.writeStream.format("memory")
            .queryName(app_name)
            .outputMode("append")
            .start()
        )

        assert q.isActive
        q.processAllAvailable()
        df = spark.sql(f"select * from {app_name}")
        result = df.collect()
        assert len(result) == len(expecteds)
        for row in result:
            dict_row = row.asDict()
            print(dict_row)
            assert dict_row in expecteds, f"{dict_row} is not in {expecteds}"
    finally:
        q.stop()
        shutil.rmtree(file_dir)


def kafka_wrapper(
    app_name: str,
    brokers: str,
    process: Callable[[List[DataFrame]], DataFrame],
    inputs: List[Tuple[str, dict]],
    spark: SparkSession,
) -> DataFrame:
    dfs = [
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", brokers)
        .option("subscribe", topic)
        .load()
        .selectExpr("CAST(value AS STRING) as json")
        .select(
            F.from_json(
                F.col("json"), schema=map_avro_to_spark_schema(schema["fields"])
            ).alias("data")
        )
        .select("data.*")
        for (topic, schema) in inputs
    ]
    return process(dfs)


def set_cassandra(
    # cassandra_ip: str,
    # cassandra_port: str,
    # cassandra_user: str,
    # cassandra_password: str,
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
    inputs: List[Tuple[str, dict]],
    spark: SparkSession,
) -> DataFrame:
    # spark = SparkSession.builder.appName(app_name).getOrCreate()
    dfs = [
        spark.readStream.schema(map_avro_to_spark_schema(schema["fields"]))
        .option("maxFileAge", max_file_age)
        .json(location)
        for (location, schema) in inputs
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
