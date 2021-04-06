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

import org.apache.spark.sql.streaming.Trigger

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
object ReplayHistoryFromFile {
  def main(args: Array[String]): Unit = {
    if (args.length < 5) {
      System.err.println(s"""
        |Usage: FileSourceWrapper appname filelocation
        |  <appname> is the name of the app
        |  <brokers> is a list of one or more Kafka brokers
        |  <outputTopic> is the kafka topic to produce to
        |  <filelocations> is a comma seperated locations for the filestore
        |  <maxFileAge> is how far back the history should go
        |  <checkpoint> file output for streaming checkpoint
        |  <cassandraTable> cassandra table to write to (schema.table_version)
        |  <cassandraCluster> cassandra cluster name
        """.stripMargin)
      System.exit(1)
    }

    StreamingExamples.setStreamingLogLevels()

    val Array(
      appName,
      //brokers,
      //outputTopic,
      fileLocations,
      maxFileAge,
      checkpoint,
      cassandraTable,
      cassandraCluster
    ) = args

    val files = fileLocations
      .split(",")
    val spark = SparkSession.builder
      .appName(appName)
      .getOrCreate()
    val user = sys.env.get("username").getOrElse("")
    val cassandraPassword = sys.env.get("password").getOrElse("")
    val cassandraIp =
      sys.env.get("CASSANDRA_LOADBALANCER_SERVICE_HOST").getOrElse("")
    val cassandraPort =
      sys.env.get("CASSANDRA_LOADBALANCER_SERVICE_PORT").getOrElse("")
    val Array(cassandraKeyspace, cassandraTableName) = cassandraTable.split("\\.")
    SparkCassandra
      .applyCassandra(
        cassandraIp,
        cassandraPort,
        user,
        cassandraPassword
      )
      .foreach({ case (key, sval) => spark.conf.set(key, sval) })

    val dfs = files
      .map(file =>
        spark.readStream
          .schema(Custom.schema)
          .option("maxFileAge", maxFileAge)
          .json(file)
      )

    val result = Custom.process(dfs)
    result.writeStream
      .outputMode(Custom.mode)
      .option("truncate", "false")
      .option("checkpointLocation", checkpoint)
      .foreachBatch { (batchDF: DataFrame, batchId: Long) =>
        batchDF.persist()
        println(batchDF.show(10)) //TODO!  make this log somewhere for debugging
        batchDF.write // Use Cassandra batch data source to write streaming out
          .format("org.apache.spark.sql.cassandra")
          .option("keyspace", cassandraKeyspace)
          .option("table", cassandraTableName)
          .option("cluster", cassandraCluster)
          .mode(
            "APPEND"
          ) //upserts if primary key already exists (exact behavior we want)
          .save()
      /*batchDF.write
          .format("kafka")
          .option("kafka.bootstrap.servers", brokers)
          .option("topic", outputTopic)
          .save()*/
      }
      .start()
      .awaitTermination()

  }
}
