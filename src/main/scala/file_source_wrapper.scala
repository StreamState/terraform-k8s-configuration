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
import org.apache.spark.sql.SparkSession

object DevFromFile {
  def main(args: Array[String]): Unit = {
    if (args.length < 5) {
      System.err.println(s"""
        |Usage: FileSourceWrapper appname filelocation
        |  <appname> is the name of the app
        |  <filelocations> is a comma seperated locations for the filestore
        |  <maxFileAge> is how far back the history should go
        |  <outputMode> one of Complete, Append, Update
        |  <checkpoint> file output for streaming checkpoint
        """.stripMargin)
      System.exit(1)
    }

    StreamingExamples.setStreamingLogLevels()

    val Array(
      appName,
      fileLocations,
      maxFileAge,
      checkpoint
    ) = args
    val files = fileLocations
      .split(",")
    val spark = SparkSession.builder
      .appName(appName)
      .getOrCreate()

    val dfs = files
      .map(file =>
        spark.readStream
          .schema(Custom.schema)
          .option("maxFileAge", maxFileAge)
          .json(file)
      )

    val result = Custom.process(dfs)
    result.writeStream
      .format("console")
      .outputMode(Custom.mode)
      .option("truncate", "false")
      .option("checkpointLocation", checkpoint)
      .start()
      .awaitTermination()

  }
}
