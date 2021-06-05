# this is for unit testing
FROM gcr.io/spark-operator/spark-py:v3.1.1-hadoop3

# Switch to user root so we can add addtional jars and configuration files.
USER root
RUN groupadd -r -g 999 sparkpy && useradd -r -g sparkpy -u 999 sparkpy

RUN pip3 install streamstate-utils==0.7.0
RUN pip3 install pyspark==3.1.1
RUN chown -R sparkpy:sparkpy $SPARK_HOME
USER sparkpy