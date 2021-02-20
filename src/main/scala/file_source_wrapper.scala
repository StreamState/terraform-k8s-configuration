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
import org.apache.spark.internal.Logging
import org.apache.spark.sql.types.{IntegerType, StringType, StructField, StructType}
/** Utility functions for Spark Streaming examples. */
object StreamingExamples extends Logging {

  /** Set reasonable logging levels for streaming if the user has not configured log4j. */
  def setStreamingLogLevels(): Unit = {
    val log4jInitialized = Logger.getRootLogger.getAllAppenders.hasMoreElements
    if (!log4jInitialized) {
      // We first log something to initialize Spark's default logging, then we override the
      // logging level.
      logInfo("Setting log level to [WARN] for streaming example." +
        " To override add a custom log4j.properties to the classpath.")
      Logger.getRootLogger.setLevel(Level.WARN)
    }
  }
}
import org.apache.kafka.clients.consumer.ConsumerConfig
import org.apache.kafka.common.serialization.StringDeserializer

import org.apache.spark.SparkConf
import org.apache.spark.streaming._
import org.apache.spark.streaming.kafka010._
import org.apache.spark.sql.SparkSession

object FileSourceWrapper {
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

    val Array(appName, fileLocations, maxFileAge, outputMode, checkpoint) = args
    val spark = SparkSession
      .builder
      .appName(appName)
      .getOrCreate()

    val schema = StructType(
      List(
        StructField("id", IntegerType, true),
        StructField("first_name", StringType, true),
        StructField("last_name", StringType, true),
        StructField("email", StringType, true),
        StructField("gender", StringType, true),
        StructField("ip_address", StringType, true),
      )
    )
    val dfs=fileLocations.split(",").map(file=>spark
      .readStream
      .schema(schema)
      //.option("path", file)
      .option("maxFileAge", maxFileAge)
      .json(file))
    
    val result=Custom.process(dfs)
    
    result.writeStream
      .format("console")
      .outputMode(outputMode)
      .option("truncate","false")
      .option("checkpointLocation", checkpoint)
      .start()
      .awaitTermination()   
    
  }
}
