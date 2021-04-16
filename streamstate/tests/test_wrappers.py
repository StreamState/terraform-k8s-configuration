from streamstate.generic_wrapper import kafka_wrapper, file_wrapper
from streamstate.run_test import helper_for_file
import pytest
from pyspark.sql import DataFrame, SparkSession
import os
import json
import shutil
from typing import List, Dict, Tuple, Callable
import pyspark.sql.functions as F
from streamstate.structs import InputStruct, SchemaStruct

# def helper_for_testing(process: Callable[[DataFrame], None], inputs: List[dict], output_mode:str):
#    inputs.
#    .writeStream.format("memory").queryName("test").outputMode(output_mode).start()


# todo, simulate local spark and local kafka
# def test_kafka_wrapper():
# assert datafrae comes back


def test_helper_for_file_succeeds(spark: SparkSession):

    helper_for_file(
        "testhelper",
        "2d",
        lambda dfs: dfs[0],
        [
            InputStruct(
                topic="topic1",
                schema=SchemaStruct(fields=[{"name": "field1", "type": "string"}]),
                sample=[{"field1": "somevalue"}],
            )
        ],
        spark,
        [{"field1": "somevalue"}],
    )


def test_helper_for_file_succeeds_multiple_topics_and_rows(spark: SparkSession):
    def process(dfs: List[DataFrame]) -> DataFrame:
        [df1, df2] = dfs
        df1 = df1.withColumn("current_timestamp", F.current_timestamp()).withWatermark(
            "current_timestamp", "2 hours"
        )
        df2 = df2.withColumn("current_timestamp", F.current_timestamp()).withWatermark(
            "current_timestamp", "2 hours"
        )
        return df1.join(
            df2,
            # F.expr(
            #      """
            # field1 = field1 AND
            # current_timestamp >= current_timestamp AND
            # current_timestamp <= current_timestamp + interval 1 hour
            # """
            # )
            (df1.field1 == df2.field1id)
            & (df1.current_timestamp >= df2.current_timestamp)
            & (
                df1.current_timestamp
                <= (df2.current_timestamp + F.expr("INTERVAL 1 HOURS"))
            ),
        ).select("field1", "value1", "value2")

    helper_for_file(
        "testhelpermultipletopics",
        "2d",
        process,
        [
            InputStruct(
                topic="topic1",
                schema=SchemaStruct(
                    fields=[
                        {"name": "field1", "type": "string"},
                        {"name": "value1", "type": "string"},
                    ]
                ),
                sample=[
                    {"field1": "somevalue", "value1": "hi1"},
                    {"field1": "somevalue1", "value1": "hi2"},
                ],
            ),
            InputStruct(
                topic="topic2",
                schema=SchemaStruct(
                    fields=[
                        {"name": "field1id", "type": "string"},
                        {"name": "value2", "type": "string"},
                    ]
                ),
                sample=[
                    {"field1id": "somevalue", "value2": "goodbye1"},
                    {"field1id": "somevalue1", "value2": "goodbye2"},
                ],
            ),
        ],
        spark,
        [
            {"field1": "somevalue", "value1": "hi1", "value2": "goodbye1"},
            {"field1": "somevalue1", "value1": "hi2", "value2": "goodbye2"},
        ],
    )


def test_helper_for_file_fails(spark: SparkSession):
    with pytest.raises(AssertionError):
        helper_for_file(
            "testhelperfails",
            "2d",
            lambda dfs: dfs[0],
            [
                InputStruct(
                    topic="topic1",
                    schema=SchemaStruct(fields=[{"name": "field1", "type": "string"}]),
                    sample=[{"field1": "somevalue1"}],
                )
            ],
            spark,
            [{"field1": "somevalue"}],
        )


def test_file_wrapper(spark: SparkSession):
    file_dir = "test_file_wrapper"
    try:
        shutil.rmtree(file_dir)
        print("folder exists, deleting")
    except:
        print("folder doesn't exist, creating")

    app_name = "mytest"
    os.mkdir(app_name)
    os.mkdir(os.path.join(app_name, file_dir))

    df = file_wrapper(
        app_name,
        "2d",
        lambda dfs: dfs[0],
        [
            InputStruct(
                topic=file_dir,
                schema=SchemaStruct(fields=[{"name": "field1", "type": "string"}]),
            )
        ],
        spark,
    )

    file_name = "localfile.json"

    data = {"field1": "somevalue"}
    file_path = os.path.join(app_name, file_dir, file_name)
    with open(file_path, mode="w") as test_file:
        json.dump(data, test_file)

    q = df.writeStream.format("memory").queryName(app_name).outputMode("append").start()
    try:
        assert q.isActive
        q.processAllAvailable()
        df = spark.sql(f"select * from {app_name}")
        result = df.collect()
        assert result[0][0] == "somevalue"
    finally:
        q.stop()
        shutil.rmtree(app_name)
