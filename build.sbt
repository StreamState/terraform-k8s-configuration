name := "direct_kafka_word_count"

scalaVersion := "2.12.12"

val sparkVersion = "3.0.1"

libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-core" % sparkVersion % "provided",
  "org.apache.spark" %% "spark-streaming" % sparkVersion % "provided",
  "org.apache.spark" %% "spark-streaming-kafka-0-10" % sparkVersion //exclude ("org.spark-project.spark", "unused")
)

assemblyJarName in assembly := name.value + ".jar"

assemblyMergeStrategy in assembly := {
    case PathList("META-INF", xs @ _*)=>MergeStrategy.discard
    case x =>MergeStrategy.last
}