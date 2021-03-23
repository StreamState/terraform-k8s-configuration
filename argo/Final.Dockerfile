FROM us.gcr.io/streamstatetest/sparkbase:v0.1.0 
COPY /tmp/streamstate.jar /opt/spark/work-dir/streamstate.jar
ENTRYPOINT ["/opt/entrypoint.sh"]