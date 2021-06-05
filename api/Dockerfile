FROM python:3.7-slim
RUN groupadd -r -g 999 restapi && useradd -r -g restapi -u 999 restapi
RUN mkdir -p /opt/restapi/work-dir
WORKDIR /opt/restapi/work-dir
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY index.py /opt/restapi/work-dir/index.py
RUN chown -R restapi:restapi /opt/restapi/work-dir
USER restapi
CMD ["uvicorn", "index:app"]