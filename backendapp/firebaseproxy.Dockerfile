FROM python:3.7-slim

RUN groupadd -r -g 999 firebase && useradd -r -g firebase -u 999 firebase
RUN pip3 install streamstate-utils==0.5.3
RUN mkdir backend
RUN mkdir -p /opt/auth/work-dir
WORKDIR /opt/auth/work-dir
ADD ../../python-docs-samples/appengine/standard/firebase/frontend /opt/auth/work-dir/
ADD ../../python-docs-samples/appengine/standard/firebase/backend /opt/auth/work-dir/
RUN chown -R firebase:firebase /opt/auth/work-dir
USER firebase
