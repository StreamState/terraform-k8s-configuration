FROM python:3.6-jessie
RUN pip3 install kubernetes 
RUN pip3 install uvicorn[standard]
RUN pip3 install fastapi
COPY sparkstreaming sparkstreaming
COPY backendapp backendapp
WORKDIR /backendapp
CMD uvicorn server:app --reload