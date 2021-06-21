ARG SPARK_VERSION=3.1.1
FROM gcr.io/spark-operator/spark-py:v${SPARK_VERSION}-hadoop3
ARG SPARK_VERSION=3.1.1
# Switch to user root so we can add addtional jars and configuration files.
USER root
RUN groupadd -r -g 999 sparkpy && useradd -r -g sparkpy -u 999 sparkpy
RUN pip3 install streamstate-utils==0.8.4
RUN mkdir -p /etc/metrics/conf
COPY sparkstreaming/metrics.properties $SPARK_HOME/conf/metrics.properties
#COPY sparkstreaming/prometheus.yaml /etc/metrics/conf


# Setup dependencies for Google Cloud Storage access.
RUN rm $SPARK_HOME/jars/guava-14.0.1.jar
ADD https://repo1.maven.org/maven2/com/google/guava/guava/23.0/guava-23.0.jar $SPARK_HOME/jars
# Add the connector jar needed to access Google Cloud Storage using the Hadoop FileSystem API.
ADD https://storage.googleapis.com/hadoop-lib/gcs/gcs-connector-latest-hadoop3.jar $SPARK_HOME/jars

ADD https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/${SPARK_VERSION}/spark-sql-kafka-0-10_2.12-${SPARK_VERSION}.jar $SPARK_HOME/jars
ADD https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/2.6.0/kafka-clients-2.6.0.jar $SPARK_HOME/jars
ADD https://repo1.maven.org/maven2/com/github/luben/zstd-jni/1.4.8-1/zstd-jni-1.4.8-1.jar $SPARK_HOME/jars
ADD https://repo1.maven.org/maven2/org/lz4/lz4-java/1.7.1/lz4-java-1.7.1.jar $SPARK_HOME/jars
ADD https://repo1.maven.org/maven2/org/slf4j/slf4j-api/1.7.30/slf4j-api-1.7.30.jar $SPARK_HOME/jars
ADD https://repo1.maven.org/maven2/org/xerial/snappy/snappy-java/1.1.8.2/snappy-java-1.1.8.2.jar $SPARK_HOME/jars
ADD https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.6.2/commons-pool2-2.6.2.jar $SPARK_HOME/jars
ADD https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/${SPARK_VERSION}/spark-token-provider-kafka-0-10_2.12-${SPARK_VERSION}.jar $SPARK_HOME/jars
ADD https://repo1.maven.org/maven2/org/spark-project/spark/unused/1.0.0/unused-1.0.0.jar $SPARK_HOME/jars
ADD https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-databind/2.10.2/jackson-databind-2.10.2.jar $SPARK_HOME/jars
ADD https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-core/2.10.2/jackson-core-2.10.2.jar $SPARK_HOME/jars

COPY streamstate_scripts/dev_app.py /opt/spark/work-dir/dev_app.py
COPY streamstate_scripts/create_folder.py /opt/spark/work-dir/create_folder.py
COPY streamstate_scripts/main_app.py /opt/spark/work-dir/main_app.py
COPY streamstate_scripts/persist_app.py /opt/spark/work-dir/persist_app.py
COPY streamstate_scripts/replay_app.py /opt/spark/work-dir/replay_app.py
RUN chown -R sparkpy:sparkpy $SPARK_HOME
USER sparkpy