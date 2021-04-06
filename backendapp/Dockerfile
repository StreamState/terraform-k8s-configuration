FROM python:3.6-jessie
RUN pip3 install kubernetes 
RUN pip3 install uvicorn[standard]
RUN pip3 install fastapi
RUN pip3 install cassandra-driver==3.24.0
RUN pip3 install avro_validator==1.0.9 
COPY sparkstreaming sparkstreaming
COPY backendapp backendapp
WORKDIR /backendapp
#CMD uvicorn server:app --reload
CMD ["uvicorn", "server:app", "--host", "0.0.0.0",  "--port", "8000"]