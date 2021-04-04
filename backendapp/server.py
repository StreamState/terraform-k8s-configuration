from fastapi import FastAPI

from initial_setup import setup_connection, create_namespace_and_service_accounts
from create_job import load_all_ymls, create_all_spark_jobs, create_replay_job
from typing import List
from request_body import Customer, Job, Table
from provision_cassandra import (
    get_cassandra_session,
    create_schema,
    list_keyspaces,
    get_data_from_table,
    create_tracking_table,
)
import os

app = FastAPI()
apiclient = setup_connection()

files = [
    "spec-templates/spark-streaming-job-template.yaml",
]

[stateful_template] = load_all_ymls(files)


@app.get("/")
def read_root():
    return {"Hello": "World"}


## TODO this should be done via github action, not the REST API
@app.post("/tenant/create")
def create_client(customer: Customer):
    result = create_namespace_and_service_accounts(apiclient, customer.name)
    return {"exceptions": result}  # if any exceptions, will be listed here


@app.post("/job/spark")
def create_spark(job: Job):
    result = create_all_spark_jobs(apiclient, stateful_template, job)
    return {"exceptions": result}  # if any exceptions, will be listed here


@app.post("/job/replay")
def create_replay(job: Job):
    result = create_replay_job(apiclient, stateful_template, job)
    return {"exceptions": result}  # if any exceptions, will be listed here


# TODO!  Dont have this in python, needs to be provisioned once for all orgs
@app.post("/database/create")
def create_track_table():
    try:
        cassandraIp = os.getenv("CASSANDRA_LOADBALANCER_SERVICE_HOST")
        cassandraPort = os.getenv("CASSANDRA_LOADBALANCER_SERVICE_PORT")
        session = get_cassandra_session(
            cassandraIp,
            cassandraPort,
            os.getenv("username"),
            os.getenv("password"),
        )
        create_tracking_table(session)
        return {"exceptions": []}
    except Exception as e:
        return {"exceptions": [str(e)]}  # if any exceptions, will be listed here


@app.post("/database/table/update")
def update_table(table: Table):
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
        version = create_schema(
            session,
            table.organization,
            table.primary_keys,
            table.avro_schema,
        )
        return {"version": version}
    except Exception as e:
        return {"exceptions": [str(e)]}  # if any exceptions, will be listed here


# make this an "admin" only function (admin per organization)
@app.get("/database/table/list/{orgname}")
def list_tables(orgname: str):
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
        return list_keyspaces(session, orgname)
        # return {"exceptions": []}  # if any exceptions, will be listed here
    except Exception as e:
        return {"exceptions": [str(e)]}  # if any exceptions, will be listed here


@app.get(
    "/database/table/get/{orgname}/{appname}/{version}"
)  # TODO, get individual records by time window or by id
def get_data(orgname: str, appname: str, version: int):
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
        return get_data_from_table(session, orgname, appname, version)
        # return {"exceptions": []}  # if any exceptions, will be listed here
    except Exception as e:
        return {"exceptions": [str(e)]}  # if any exceptions, will be listed here