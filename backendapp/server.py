from fastapi import FastAPI

from initial_setup import setup_connection, create_namespace_and_service_accounts
from create_job import load_all_ymls, create_all_spark_jobs
from typing import List
from request_body import Customer, Job

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


@app.post("/new_tenant/")
def create_client(customer: Customer):
    result = create_namespace_and_service_accounts(apiclient, customer.name)
    return {"exceptions": result}  # if any exceptions, will be listed here


@app.post("/new_job/")
def create_job(job: Job):
    result = create_all_spark_jobs(apiclient, persist_template, stateful_template, job)
    return {"exceptions": result}  # if any exceptions, will be listed here
