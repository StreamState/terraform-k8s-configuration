FROM gcr.io/spark-operator/spark-py:v3.0.0-hadoop3

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

RUN mkdir -p /etc/metrics/conf
COPY sparkstreaming/metrics.properties /etc/metrics/conf
COPY sparkstreaming/prometheus.yaml /etc/metrics/conf
USER 1001
## Todo! make this a pip-installable library
COPY streamstate /opt/spark/work-dir/streamstate
COPY setup.cfg /opt/spark/work-dir/setup.cfg
COPY setup.py /opt/spark/work-dir/setup.py
COPY VERSION /opt/spark/work-dir/VERSION