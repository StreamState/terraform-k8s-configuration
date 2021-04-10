ARG SPARK_IMAGE=gcr.io/spark-operator/spark:v3.0.0-hadoop3
FROM ${SPARK_IMAGE}

# Set up dependencies for Google Cloud Storage access.
RUN rm $SPARK_HOME/jars/guava-14.0.1.jar
ADD http://repo1.maven.org/maven2/com/google/guava/guava/23.0/guava-23.0.jar $SPARK_HOME/jars
# Add the connector jar needed to access Google Cloud Storage using the Hadoop FileSystem API.
ADD https://storage.googleapis.com/hadoop-lib/gcs/gcs-connector-latest-hadoop3.jar $SPARK_HOME/jars

ENTRYPOINT ["/opt/entrypoint.sh"]