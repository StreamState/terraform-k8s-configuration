from fastapi import FastAPI

from initial_setup import setup_connection, create_namespace_and_service_accounts
from create_job import load_all_ymls, create_all_spark_jobs
from typing import List
from request_body import Customer, Job, Table
from provision_cassandra import get_cassandra_session, create_schema
import os

app = FastAPI()
apiclient = setup_connection()

files = [
    "../sparkstreaming/spark-streaming-file-persist-template.yaml",
    "../sparkstreaming/spark-streaming-job-template.yaml",
]

[persist_template, stateful_template] = load_all_ymls(files)


@app.get("/")
def read_root():
    return {"Hello": "World"}


## TODO this should be done via github action, not the REST API
@app.post("/new_tenant/")
def create_client(customer: Customer):
    result = create_namespace_and_service_accounts(apiclient, customer.name)
    return {"exceptions": result}  # if any exceptions, will be listed here


@app.post("/new_job/")
def create_job(job: Job):
    result = create_all_spark_jobs(apiclient, persist_template, stateful_template, job)
    return {"exceptions": result}  # if any exceptions, will be listed here


@app.post("/new_database/")
def create_database(table: Table):
    try:
        session = get_cassandra_session(os.getenv("username"), os.getenv("password"))
        create_schema(session, table.namespace, table.app_name)
        return {"exceptions": []}  # if any exceptions, will be listed here
    except Exception as e:
        return {"exceptions": [str(e)]}  # if any exceptions, will be listed here
