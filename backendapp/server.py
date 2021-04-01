from fastapi import FastAPI

from initial_setup import setup_connection, create_namespace_and_service_accounts
from create_job import load_all_ymls, create_all_spark_jobs
from typing import List
from request_body import Customer, Job, Table
from provision_cassandra import get_cassandra_session, create_schema, list_keyspaces
import os

app = FastAPI()
apiclient = setup_connection()

files = [
    "spec-templates/spark-streaming-file-persist-template.yaml",
    "spec-templates/sparkstreaming/spark-streaming-job-template.yaml",
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
    # this requires the load balances to be set up, once it does apparently
    # gke injects these env variables in each container that is created
    cassandraIp = os.getenv("CASSANDRA_LOADBALANCER_SERVICE_HOST")
    cassandraPort = os.getenv("CASSANDRA_LOADBALANCER_SERVICE_PORT")
    try:
        session = get_cassandra_session(
            cassandraIp,
            cassandraPort,
            os.getenv("username"),
            os.getenv("password"),
        )
        create_schema(session, table.namespace, table.app_name)
        return {"exceptions": []}  # if any exceptions, will be listed here
    except Exception as e:
        return {"exceptions": [str(e)]}  # if any exceptions, will be listed here


# make this an "admin" only function (admin per organization)
@app.post("/list_tables/")
def list_tables(table: Table):
    # this requires the load balances to be set up, once it does apparently
    # gke injects these env variables in each container
    cassandraIp = os.getenv("CASSANDRA_LOADBALANCER_SERVICE_HOST")
    cassandraPort = os.getenv("CASSANDRA_LOADBALANCER_SERVICE_PORT")
    try:
        session = get_cassandra_session(
            cassandraIp,
            cassandraPort,
            os.getenv("username"),
            os.getenv("password"),
        )
        list_keyspaces(session, table.namespace)
        return {"exceptions": []}  # if any exceptions, will be listed here
    except Exception as e:
        return {"exceptions": [str(e)]}  # if any exceptions, will be listed here


@app.post("/new_table/")
def create_table(table: Table):
    # this requires the load balances to be set up, once it does apparently
    # gke injects these env variables in each container that is created
    cassandraIp = os.getenv("CASSANDRA_LOADBALANCER_SERVICE_HOST")
    cassandraPort = os.getenv("CASSANDRA_LOADBALANCER_SERVICE_PORT")
    try:
        session = get_cassandra_session(
            cassandraIp,
            cassandraPort,
            os.getenv("username"),
            os.getenv("password"),
        )
        create_schema(session, table.namespace, table.app_name, table.db_schema)
        return {"exceptions": []}  # if any exceptions, will be listed here
    except Exception as e:
        return {"exceptions": [str(e)]}  # if any exceptions, will be listed here