FROM python:3.7-slim
RUN groupadd -r -g 999 firestore && useradd -r -g firestore -u 999 firestore
RUN pip3 install streamstate-utils==0.7.0
RUN mkdir -p /opt/firestore/work-dir
WORKDIR /opt/firestore/work-dir
COPY entrypoint.py /opt/firestore/work-dir/entrypoint.py
COPY provision_firestore.py /opt/firestore/work-dir/provision_firestore.py
RUN chown -R firestore:firestore /opt/firestore/work-dir
USER firestore