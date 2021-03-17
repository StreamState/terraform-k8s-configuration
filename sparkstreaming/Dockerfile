FROM hseeberger/scala-sbt:graalvm-ce-20.0.0-java11_1.3.13_2.12.12 AS build
COPY src src
COPY build.sbt build.sbt
COPY project/assembly.sbt project/assembly.sbt
COPY project/build.properties project/build.properties
RUN sbt assembly

FROM gcr.io/spark-operator/spark:v3.0.0-hadoop3

# Switch to user root so we can add addtional jars and configuration files.
USER root

# Setup dependencies for Google Cloud Storage access.
RUN rm $SPARK_HOME/jars/guava-14.0.1.jar
ADD https://repo1.maven.org/maven2/com/google/guava/guava/23.0/guava-23.0.jar $SPARK_HOME/jars
RUN chmod 644 $SPARK_HOME/jars/guava-23.0.jar
# Add the connector jar needed to access Google Cloud Storage using the Hadoop FileSystem API.
ADD https://storage.googleapis.com/hadoop-lib/gcs/gcs-connector-latest-hadoop3.jar $SPARK_HOME/jars
RUN chmod 644 $SPARK_HOME/jars/gcs-connector-latest-hadoop3.jar

# Setup for the Prometheus JMX exporter.
# Add the Prometheus JMX exporter Java agent jar for exposing metrics sent to the JmxSink to Prometheus.
ADD https://repo1.maven.org/maven2/io/prometheus/jmx/jmx_prometheus_javaagent/0.11.0/jmx_prometheus_javaagent-0.11.0.jar /prometheus/
RUN chmod 644 /prometheus/jmx_prometheus_javaagent-0.11.0.jar

USER ${spark_uid}

RUN mkdir -p /etc/metrics/conf
COPY sparkstreaming/metrics.properties /etc/metrics/conf
COPY sparkstreaming/prometheus.yaml /etc/metrics/conf
COPY --from=build /root/target/scala-2.12/kafka_and_file_connect.jar /opt/spark/work-dir/streamstate.jar

ENTRYPOINT ["/opt/entrypoint.sh"]



#FROM gcr.io/spark-operator/spark:v3.0.0-gcs-prometheus
#RUN mkdir -p /opt/hadoop/conf
#COPY sparkstreaming/core-site.xml /opt/hadoop/conf/core-site.xml
#COPY sparkstreaming/spark-env.sh $SPARK_HOME/conf/spark-env.sh
#ENTRYPOINT [ "/opt/entrypoint.sh" ]