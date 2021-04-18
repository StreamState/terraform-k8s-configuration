## THIS IS DEPRICATED
## This does two things: ensures custom functions pass tests AND 
# since its arbitrary code ensures that its valid Python

## future, we want to pip install this rather than copy it in
## only copy in the python "process" script (custom code)

## the deployment of the python library code will be via streamstate 
## repo, not via client repo
FROM openjdk:11-jre-slim-buster
RUN apt-get update
RUN apt-get install python3 -y
RUN apt-get install python3-venv -y
RUN groupadd -r -g 999 unittest && useradd -r -g unittest -u 999 unittest
RUN mkdir /opt/python  && chown unittest:unittest /opt/python
WORKDIR /opt/python
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ADD streamstate streamstate
ADD setup.cfg setup.cfg
ADD setup.py setup.py 
ADD README.md README.md
ADD VERSION VERSION
RUN python3 setup.py install
RUN chmod 757 -R /opt/python/* 

USER unittest 

#"[{\"folder\":\"topic1\", \"sample\":[{\"field1\": \"somevalue\"}], \"schema\": {\"fields\": [{\"name\": \"field1\", \"type\": \"string\"}]}}]"

#"[{\"field1\": \"somevalue\"}]" 

#curl -H "Content-Type: application/json" -X POST -d "{\"pythoncode\":\"$(base64 -w 0 ./streamstate/process.py)\", \"inputs\":[{\"folder\":\"topic1\", \"sample\":[{\"field1\": \"somevalue\"}], \"schema\": {\"fields\": [{\"name\": \"field1\", \"type\": \"string\"}]}}], \"assertions\":[{\"field1\": \"somevalue\"}]}" http://localhost:12000/build/container


#curl -H "Content-Type: application/json" -X POST -d "{\"pythoncode\":\"$(base64 -w 0 ./streamstate/process.py)\", \"inputs\":\"$(base64 -w 0 ./streamstate/sampleinputs.json)\", \"assertions\":\"$(base64 -w 0 ./streamstate/assertedoutputs.json)\"}" http://localhost:12000/build/container