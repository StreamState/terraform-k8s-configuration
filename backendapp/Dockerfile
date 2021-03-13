FROM python:3.6-jessie
RUN pip3 install kubernetes 
COPY sparkstreaming sparkstreaming
COPY backendapp backendapp
WORKDIR /backendapp
CMD python -m http.server 8000