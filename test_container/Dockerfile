#FROM gcr.io/spark-operator/spark:v3.0.0
FROM bde2020/spark-master:3.0.1-hadoop3.2
ENV SCALA_VERSION 2.12.12
ENV SBT_VERSION 1.4.7

ENV PATH /sbt/bin:$PATH

RUN apk add -U bash docker
RUN mkdir scala
WORKDIR /scala
RUN adduser --home /home/developer --shell /bin/bash --disabled-password developer
# Install Scala
## Piping curl directly in tar
RUN \
  wget -O - https://downloads.typesafe.com/scala/$SCALA_VERSION/scala-$SCALA_VERSION.tgz | tar xfz - -C /scala && \
  echo >> /home/developer/.bashrc && \
  echo "export PATH=/scala/scala-$SCALA_VERSION/bin:$PATH" >> /home/developer/.bashrc && \
  echo "export PATH=/scala/sbt/bin:$PATH" >> /home/developer/.bashrc && \
  echo "export PATH=/spark/bin:$PATH" >> /home/developer/.bashrc

# Install SBT
RUN wget -O - https://github.com/sbt/sbt/releases/download/v$SBT_VERSION/sbt-$SBT_VERSION.tgz | tar xfz - -C /scala

USER developer
WORKDIR /home/developer
RUN /scala/sbt/bin/sbt sbtVersion
ADD build.sbt .
ADD src src
ADD project/assembly.sbt project/assembly.sbt
RUN /scala/sbt/bin/sbt assembly
RUN mkdir tmp_file