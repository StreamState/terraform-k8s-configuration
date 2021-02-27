name := "kafka_and_file_connect"

scalaVersion := "2.12.12"

val sparkVersion = "3.0.0"

libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-core" % sparkVersion % "provided",
  "org.apache.spark" %% "spark-sql" % sparkVersion % "provided",
  "org.apache.spark" %% "spark-streaming" % sparkVersion % "provided",
  "org.apache.spark" %% "spark-streaming-kafka-0-10" % sparkVersion, //exclude ("org.spark-project.spark", "unused")
  "org.apache.spark" %% "spark-sql-kafka-0-10" % sparkVersion,
  "com.datastax.spark" %% "spark-cassandra-connector" % sparkVersion
)

assemblyJarName in assembly := name.value + ".jar"

assemblyMergeStrategy in assembly := {
  case PathList("META-INF", xs @ _*) => MergeStrategy.discard
  case x                             => MergeStrategy.last
}
