package sparkwrappers
import org.apache.log4j.{Level, Logger}
import org.apache.spark.internal.Logging
import org.apache.spark.{SparkConf}

/** Utility functions for Spark Streaming examples. */
object StreamingExamples extends Logging {

  /** Set reasonable logging levels for streaming if the user has not configured log4j. */
  def setStreamingLogLevels(): Unit = {
    val log4jInitialized = Logger.getRootLogger.getAllAppenders.hasMoreElements
    if (!log4jInitialized) {
      // We first log something to initialize Spark's default logging, then we override the
      // logging level.
      logInfo(
        "Setting log level to [WARN] for streaming example." +
          " To override add a custom log4j.properties to the classpath."
      )
      Logger.getRootLogger.setLevel(Level.WARN)
    }
  }
}

object SparkCassandra {
  def applyCassandra(
      cassandraIp: String,
      cassandraPort: String,
      cassandraUser: String,
      cassandraPassword: String
  ): Seq[(String, String)] = {
    Seq(
      ("spark.cassandra.connection.host", cassandraIp),
      ("spark.cassandra.connection.port", cassandraPort),
      ("spark.cassandra.auth.username", cassandraUser),
      ("spark.cassandra.auth.password", cassandraPassword)
    )
  }
}
