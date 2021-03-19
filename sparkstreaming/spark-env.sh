# see https://github.com/GoogleCloudPlatform/spark-on-k8s-gcp-examples/blob/master/conf/spark-env.sh
export HADOOP_CONF_DIR="/opt/hadoop/conf"
export HADOOP_OPTS="$HADOOP_OPTS -Dgs.project.id=$GS_PROJECT_ID"