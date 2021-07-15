# this is for unit testing
ARG SPARK_VERSION=3.1.1
FROM gcr.io/spark-operator/spark-py:v${SPARK_VERSION}-hadoop3

ARG SPARK_VERSION=3.1.1
# Switch to user root so we can add addtional jars and configuration files.
USER root
RUN groupadd -r -g 999 sparkpy && useradd -r -g sparkpy -u 999 sparkpy

RUN pip3 install streamstate-utils==0.9.0
RUN pip3 install pyspark==${SPARK_VERSION}
RUN chown -R sparkpy:sparkpy $SPARK_HOME
USER sparkpy