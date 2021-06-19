FROM gcr.io/spark-operator/spark-py:v3.1.1-hadoop3

# Switch to user root so we can add addtional jars and configuration files.
USER root
RUN groupadd -r -g 999 sparkpy && useradd -r -g sparkpy -u 999 sparkpy
RUN pip3 install streamstate-utils==0.8.3
RUN mkdir -p /etc/metrics/conf
COPY sparkstreaming/metrics.properties $SPARK_HOME/conf/metrics.properties
#COPY sparkstreaming/prometheus.yaml /etc/metrics/conf


# Setup dependencies for Google Cloud Storage access.
RUN rm $SPARK_HOME/jars/guava-14.0.1.jar
ADD https://repo1.maven.org/maven2/com/google/guava/guava/23.0/guava-23.0.jar $SPARK_HOME/jars
# Add the connector jar needed to access Google Cloud Storage using the Hadoop FileSystem API.
ADD https://storage.googleapis.com/hadoop-lib/gcs/gcs-connector-latest-hadoop3.jar $SPARK_HOME/jars

COPY streamstate_scripts/dev_app.py /opt/spark/work-dir/dev_app.py
COPY streamstate_scripts/create_folder.py /opt/spark/work-dir/create_folder.py
COPY streamstate_scripts/main_app.py /opt/spark/work-dir/main_app.py
COPY streamstate_scripts/persist_app.py /opt/spark/work-dir/persist_app.py
COPY streamstate_scripts/replay_app.py /opt/spark/work-dir/replay_app.py
RUN chown -R sparkpy:sparkpy $SPARK_HOME
USER sparkpy