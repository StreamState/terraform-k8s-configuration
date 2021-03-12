FROM python:3.6-jessie
COPY backendapp backendapp
COPY sparkstreaming sparkstreaming
WORKDIR /backendapp
RUN pip3 install kubernetes 
CMD python -m http.server 8000