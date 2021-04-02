from cassandra.cluster import Cluster, Session
from cassandra.auth import PlainTextAuthProvider
import os
from kubernetes.client.api_client import ApiClient
from kubernetes.client.api import CoreV1Api
import subprocess
from typing import List, Dict, Tuple, Union

## use REST api to call this on initial project creation


def get_cassandra_session(ip: str, port: int, user: str, password: str) -> Session:
    auth_provider = PlainTextAuthProvider(
        username=user,
        password=password,
    )
    cluster = Cluster([ip], port=port, auth_provider=auth_provider)
    return cluster.connect()


def _get_existing_fields(
    session: Session, org_name: str, app_name: str
) -> Dict[str, str]:
    rows = session.execute(
        f"""
        SELECT column_name, type FROM system_schema.columns
        WHERE keyspace_name = '{org_name}' AND table_name = '{app_name}';
    """
    )
    return dict([(row.column_name, row.type) for row in rows])


def _alter_requirements(
    existing_columns: Dict[str, str], schema_fields: Dict[str, str]
) -> List[Tuple[str, str, str]]:
    updates: List[Tuple[str, str, str]] = []
    for key in schema_fields:
        existing_col = existing_columns.get(key)
        if existing_col:
            if schema_fields[key] != existing_col:
                updates.append((key, schema_fields[key], "alter"))
        else:
            updates.append((key, schema_fields[key], "add"))
    return updates


def generate_alter(org_name: str, app_name: str, key: str, col_type: str) -> str:
    return f"ALTER {org_name}.{app_name} ALTER {key} TYPE {col_type}"


def generate_create(org_name: str, app_name: str, key: str, col_type: str) -> str:
    return f"ALTER {org_name}.{app_name} ADD {key} {col_type}"


def generate_new_table(
    org_name: str, app_name: str, schema: Dict[str, Union[Dict[str, str], List[str]]]
) -> List[str]:
    fields = schema["fields"]
    if isinstance(fields, dict):  # to get pass type checker
        field_list = ",".join(
            [f"{key} {col_type}" for (key, col_type) in fields.items()]
        )
    primary_keys = ",".join(schema["primary_keys"])
    return [
        f"CREATE TABLE {org_name}.{app_name} ({field_list}, PRIMARY KEY ({primary_keys}));"
    ]


def generate_ddl(
    org_name: str,
    app_name: str,
    existing_columns: Dict[str, str],
    schema: Dict[str, str],
) -> List[str]:
    updates = _alter_requirements(existing_columns, schema)
    return [
        generate_alter(org_name, app_name, r[0], r[1])
        if r[2] == "alter"
        else generate_create(org_name, app_name, r[0], r[1])
        for r in updates
    ]


def _validate_schema(schema: Dict[str, Union[Dict[str, str], List[str]]]):
    assert schema["primary_keys"]
    assert schema["fields"]
    assert isinstance(schema["fields"], dict)
    assert isinstance(schema["primary_keys"], list)


def apply_table(
    session: Session,
    org_name: str,
    app_name: str,
    schema: Dict[str, Union[Dict[str, str], List[str]]],
):
    existing_fields = _get_existing_fields(session, org_name, app_name)
    schema_fields = schema["fields"]
    result: List[str] = []
    if existing_fields:  # then table already exists
        if isinstance(schema_fields, dict):  # to get pass type checker
            result = generate_ddl(org_name, app_name, existing_fields, schema_fields)
    else:
        result = generate_new_table(org_name, app_name, schema)
    for r in result:
        session.execute(r)


def create_schema(
    session: Session,
    org_name: str,
    app_name: str,
    schema: Dict[str, Union[Dict[str, str], List[str]]],
):
    create_keyspace = f"CREATE KEYSPACE IF NOT EXISTS {org_name} WITH replication = {{ 'class' : 'NetworkTopologyStrategy', 'dc1' : '1' }};"
    print(f"running query {create_keyspace}")
    session.execute(create_keyspace)
    _validate_schema(schema)
    apply_table(session, org_name, app_name, schema)


def list_keyspaces(session: Session, org_name: str) -> dict:
    tables = session.execute(
        f"SELECT * FROM system_schema.tables WHERE keyspace_name = '{org_name}';"
    )
    return {"tables": tables}


def get_data_from_table(session: Session, orgname: str, table_name: str) -> dict:
    fields = session.execute(f"SELECT * FROM {orgname}.{table_name};")
    return {"fields": fields}