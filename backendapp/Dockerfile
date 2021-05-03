FROM python:3.7-slim
RUN groupadd -r -g 999 cassandra && useradd -r -g cassandra -u 999 cassandra
#RUN pip3 install cassandra-driver==3.24.0
#RUN pip3 install avro_validator==1.0.9 
RUN pip3 install streamstate-utils==0.5.3
RUN mkdir backend
RUN mkdir -p /opt/cassandra/work-dir
WORKDIR /opt/cassandra/work-dir
COPY entrypoint.py /opt/cassandra/work-dir/entrypoint.py
COPY provision_cassandra.py /opt/cassandra/work-dir/provision_cassandra.py
COPY provision_firestore.py /opt/cassandra/work-dir/provision_firestore.py
RUN chown -R cassandra:cassandra /opt/cassandra/work-dir
USER cassandra