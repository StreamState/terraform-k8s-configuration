FROM python:3.6-jessie
RUN pip3 install kubernetes 
RUN pip3 install uvicorn[standard]
RUN pip3 install fastapi
RUN pip3 install cassandra-driver==3.24.0
COPY sparkstreaming sparkstreaming
COPY backendapp backendapp
WORKDIR /backendapp
CMD uvicorn server:app --reload