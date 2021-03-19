/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// scalastyle:off println
package sparkwrappers
import org.apache.log4j.{Level, Logger}
import org.apache.spark.sql.streaming.Trigger
import org.apache.spark.internal.Logging

import org.apache.spark.sql.functions.{from_json, col}
import org.apache.kafka.clients.consumer.ConsumerConfig
import org.apache.kafka.common.serialization.StringDeserializer

import org.apache.spark.SparkConf
import org.apache.spark.streaming._
import org.apache.spark.streaming.kafka010._
import org.apache.spark.sql.{SparkSession, DataFrame}

import org.apache.spark.sql.cassandra._

import com.datastax.spark.connector.cql.CassandraConnectorConf
import com.datastax.spark.connector.rdd.ReadConf
import com.datastax.spark.connector._

/** Consumes messages from one or more topics in Kafka and does wordcount.
  * Usage: DirectKafkaWordCount <brokers> <topics>
  *   <brokers> is a list of one or more Kafka brokers
  *   <groupId> is a consumer group name to consume from topics
  *   <topics> is a list of one or more kafka topics to consume from
  *
  * Example:
  *    $ bin/run-example streaming.DirectKafkaWordCount broker1-host:port,broker2-host:port \
  *    consumer-group topic1,topic2
  */
object KafkaSourceWrapper {
  def main(args: Array[String]): Unit = {
    if (args.length < 9) {
      System.err.println(s"""
        |Usage: KafkaSourceWrapper <brokers> <groupId> <topics>
        |  <appName> spark app name
        |  <brokers> is a list of one or more Kafka brokers
        |  <outputTopic> is the kafka topic to produce to
        |  <groupId> is a consumer group name to consume from topics
        |  <topics> is a list of one or more kafka topics to consume from
        |  <checkpoint> file output for streaming checkpoint
        |  <cassandraCluster> cassandra cluster name
        |  <cassandraIp> ip address of cassandra cluster 
        |  <cassandraPassword> password of cassandra cluster
        """.stripMargin)
      System.exit(1)
    }

    StreamingExamples.setStreamingLogLevels()

    val Array(
      appName,
      brokers,
      outputTopic,
      groupId,
      topics,
      checkpoint,
      cassandraCluster,
      cassandraIp
    ) = args
    val spark = SparkSession.builder
      .appName(appName)
      .getOrCreate()
    val user = sys.env.get("username").getOrElse("")
    val cassandraPassword = sys.env.get("password").getOrElse("")
    SparkCassandra
      .applyCassandra(
        cassandraIp,
        "9042",
        user,
        cassandraPassword
      )
      .foreach({ case (key, sval) => spark.conf.set(key, sval) })

    //https://docs.databricks.com/spark/latest/structured-streaming/kafka.html
    /** .option("kafka.ssl.truststore.location", <dbfs-truststore-location>) \
      *  .option("kafka.ssl.keystore.location", <dbfs-keystore-location>) \
      *  .option("kafka.ssl.keystore.password", dbutils.secrets.get(scope=<certificate-scope-name>,key=<keystore-password-key-name>)) \
      *  .option("kafka.ssl.truststore.password", dbutils.secrets.get(scope=<certificate-scope-name>,key=<truststore-password-key-name>))
      */
    val dfs = topics
      .split(",")
      .map(topic =>
        spark.readStream
          .format("kafka")
          .option("kafka.bootstrap.servers", brokers)
          .option("subscribe", topic)
          .load()
          .selectExpr("CAST(value AS STRING) as json")
          .select(from_json(col("json"), schema = Custom.schema).as("data"))
          .select("data.*")
      )

    val result = Custom.process(dfs)

    result.writeStream
      .outputMode(Custom.mode)
      .option("truncate", "false")
      .option("checkpointLocation", checkpoint)
      .foreachBatch { (batchDF: DataFrame, batchId: Long) =>
        batchDF.persist()
        println(batchDF.show(10)) //TODO!  make this log somewhere for debugging
        //write to cassandra
        batchDF.write // Use Cassandra batch data source to write streaming out
          .format("org.apache.spark.sql.cassandra")
          .option("keyspace", "cycling")
          .option("table", "cyclist_semi_pro")
          .option("cluster", cassandraCluster)
          .mode(
            "APPEND"
          ) //upserts if primary key already exists (exact behavior we want)
          .save()
        //write to kafka
        batchDF.write
          .format("kafka")
          .option("kafka.bootstrap.servers", brokers)
          .option("topic", outputTopic)
          .save()
      }
      .start()
      .awaitTermination()
  }
}
