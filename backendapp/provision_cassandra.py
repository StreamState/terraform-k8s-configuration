from cassandra.cluster import Cluster, Session
from cassandra.auth import PlainTextAuthProvider
import os

import subprocess

## use REST api to call this on initial project creation


def get_cassandra_session(user: str, password: str) -> Session:
    auth_provider = PlainTextAuthProvider(
        username=user,
        password=password,
    )
    cluster = Cluster(["127.0.0.1"], port=30500, auth_provider=auth_provider)
    return cluster.connect()


# need to pass the output schema here to create the appropriate structure
def create_schema(session: Session, org_name: str, app_name: str):
    session.execute(
        f"CREATE KEYSPACE IF NOT EXISTS {org_name} WITH replication = {{ 'class' : 'NetworkTopologyStrategy', 'dc1' : '1' }};"
    )
    session.execute(
        f"""CREATE TABLE IF NOT EXISTS {org_name}.{app_name} (
        first_name text, 
        last_name text, 
        PRIMARY KEY (last_name));"""
    )
