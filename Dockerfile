from gcr.io/spark-operator/spark:v3.0.0
COPY target/scala-2.12/direct_kafka_word_count.jar /opt/spark/work-dir
