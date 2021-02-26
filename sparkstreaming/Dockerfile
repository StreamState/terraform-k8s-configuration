FROM hseeberger/scala-sbt:graalvm-ce-20.0.0-java11_1.3.13_2.12.12 AS build
COPY src src
COPY build.sbt build.sbt
COPY project/assembly.sbt project/assembly.sbt
COPY project/build.properties project/build.properties
RUN sbt assembly

FROM gcr.io/spark-operator/spark:v3.0.0
COPY --from=build /root/target/scala-2.12/*.jar /opt/spark/work-dir/sparkstreaming.jar
