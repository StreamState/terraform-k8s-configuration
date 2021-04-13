FROM wurstmeister/kafka:2.13-2.7.0
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

ADD streamstate streamstate
#RUN pip3 install pyspark==3.0.1

