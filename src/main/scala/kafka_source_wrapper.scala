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
package dhstest
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
    if (args.length < 4) {
      System.err.println(s"""
        |Usage: KafkaSourceWrapper <brokers> <groupId> <topics>
        |  <brokers> is a list of one or more Kafka brokers
        |  <groupId> is a consumer group name to consume from topics
        |  <topics> is a list of one or more kafka topics to consume from
        |  <outputMode> one of Complete, Append, Update
        |  <sink> file output for kafka sink
        |  <checkpoint> file output for streaming checkpoint
        """.stripMargin)
      System.exit(1)
    }

    StreamingExamples.setStreamingLogLevels()

    val Array(brokers, groupId, topics, outputMode, sink, checkpoint, cassandraIp, cassandraPassword) = args
    val spark = SparkSession.builder
      .appName("DirectKafkaWordCount")
      .getOrCreate()
    val clusterName = "cluster1" //see cassandra/datacenter.yaml

 
    spark.conf.set("spark.cassandra.connection.host",cassandraIp)
    spark.conf.set("spark.cassandra.connection.port","9042")
    spark.conf.set("spark.cassandra.auth.username","cluster1-superuser")
    spark.conf.set(
      "spark.cassandra.auth.password",
      cassandraPassword
    )
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

    //so we keep a record in case we need to replay history
    dfs.foreach(df =>
      df.writeStream
        .format("json") // can be "orc", "json", "csv", etc.
        .outputMode("Append")
        .option("checkpointLocation", checkpoint)
        .trigger(
          Trigger.ProcessingTime("2 seconds")
        ) //only write every so often
        .option("path", sink)
        .start()
    )

    /*result.writeStream
      .format("org.apache.spark.sql.cassandra")
      .option("keyspace", "cycling")
      .option("table", "cyclist_semi_pro")
      .option("checkpointLocation", checkpoint)

      //.cassandraFormat("cyclist_semi_pro", "cycling")
      .outputMode(outputMode)
      .start()*/

    result.writeStream
      //.format("console")
      .outputMode(outputMode)
      .option("truncate", "false")
      .option("checkpointLocation", checkpoint)
      .foreachBatch { (batchDF: DataFrame, batchId: Long) =>
      	batchDF.persist() 
      	println(batchDF.show(10))
        batchDF.write // Use Cassandra batch data source to write streaming out
          .format("org.apache.spark.sql.cassandra")
          .option("keyspace", "cycling")
          .option("table", "cyclist_semi_pro")
          .option("cluster", clusterName)
          .mode("APPEND")
          .save()
      }
      .start().awaitTermination()
   //spark.streams.awaitAnyTermination()

  }
}
