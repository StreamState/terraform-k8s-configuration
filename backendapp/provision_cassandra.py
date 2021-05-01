from cassandra.cluster import Cluster, Session
from cassandra.auth import PlainTextAuthProvider
from typing import List, Dict, Tuple
from streamstate_utils.cassandra_utils import (
    get_cassandra_key_space_from_org_name,
    get_cassandra_table_name_from_app_name,
)

import json
from avro_validator.schema import Schema, RecordType

from streamstate_utils.structs import CassandraInputStruct


def get_cassandra_session(
    cassandra_input: CassandraInputStruct,
) -> Tuple[Cluster, Session]:
    auth_provider = PlainTextAuthProvider(
        username=cassandra_input.cassandra_user,
        password=cassandra_input.cassandra_password,
    )
    cluster = Cluster(
        [cassandra_input.cassandra_ip],
        port=cassandra_input.cassandra_port,
        auth_provider=auth_provider,
    )
    return cluster, cluster.connect()


def get_existing_schema(
    session: Session, org_name: str, app_name: str
) -> Tuple[str, int]:
    rows = session.execute(
        f"""
        SELECT avroschema, version FROM admin_track.track_schema_current 
        WHERE organization = '{org_name}' and appname='{app_name}';
    """
    ).current_rows
    if len(rows) == 0:
        return "", 0
    else:
        [row] = rows
        return row.avroschema, row.version


def _parse_schema(schema: List[Dict[str, str]]):
    for field in schema:
        assert "name" in field
        assert "type" in field
        assert type(field["name"]) == str
        assert type(field["type"]) == str


def _convert_type(avro_type: str) -> str:
    avro_type_conversion = {
        "boolean": "boolean",
        "int": "int",
        "long": "bigint",
        "float": "float",  # safe side
        "double": "double",
        "string": "text",
    }
    return avro_type_conversion[avro_type]


def apply_table(
    session: Session,
    org_name: str,
    app_name: str,
    version: int,
    primary_keys: List[str],
    fields: List[Dict[str, str]],
):
    field_list = ",".join(
        [field["name"] + " " + _convert_type(field["type"]) for field in fields]
    )
    primary_key_str = ",".join(primary_keys)
    key_space = get_cassandra_key_space_from_org_name(org_name)
    table_name = get_cassandra_table_name_from_app_name(app_name, version)
    full_table_name = f"{key_space}.{table_name}"
    sql = f"""
        CREATE TABLE {full_table_name} ({field_list}, 
        PRIMARY KEY ({primary_key_str}));
    """
    session.execute(sql)


# TODO: probably should NOT be in python (maybe provision from terraform?  or rest of github action?)
# one table for ALL organizations
# TODO: change dc1 to actual data center!!
def create_tracking_table(session: Session):
    sql = """
        CREATE KEYSPACE IF NOT EXISTS admin_track WITH 
        replication = { 'class' : 'NetworkTopologyStrategy', 'dc1' : '1' };
    """
    session.execute(sql)
    sql = """
        CREATE TABLE IF NOT EXISTS  admin_track.track_schema_history 
        (avroschema text, organization text, appname text,
         version int, PRIMARY KEY(organization, appname, version)
        );
    """
    session.execute(sql)
    sql = """
        CREATE TABLE IF NOT EXISTS admin_track.track_schema_current
        (avroschema text, organization text, 
        appname text, version int, PRIMARY KEY(organization, appname));
    """
    session.execute(sql)


def insert_tracking_table(
    session: Session, org_name: str, app_name: str, avro_schema: str, version: int
):
    sql = f"""
        INSERT INTO admin_track.track_schema_history (avroschema, organization, appname, version)
        VALUES ('{avro_schema}', '{org_name}', '{app_name}', {version});
    """
    session.execute(sql)
    # same as upsert, essentially
    sql = f"""
        UPDATE admin_track.track_schema_current 
        set avroschema='{avro_schema}', version={version}
        where organization='{org_name}' and appname='{app_name}';
    """
    session.execute(sql)


def _sublist(ls1: List[str], ls2: List[str]) -> bool:
    for x in ls1:
        if x not in ls2:
            return False
    return True


def create_schema(
    session: Session,
    org_name: str,
    app_name: str,
    primary_keys: List[str],
    schema: List[Dict[str, str]],  # name: fieldname, type: datatype
):
    # will throw if schema isn't valid
    _parse_schema(schema)
    # app_name = schema["name"]
    field_names = [field["name"] for field in schema]
    assert _sublist(primary_keys, field_names)
    prev_schema, prev_version = get_existing_schema(session, org_name, app_name)
    schema_as_string = json.dumps(schema)
    if prev_schema != schema_as_string:
        version = prev_version + 1
        # TODO!  Figure out replication needs
        # TODO: change dc1 to actual data center!!
        create_keyspace = f"""
            CREATE KEYSPACE IF NOT EXISTS {org_name} 
            WITH replication = {{ 'class' : 'NetworkTopologyStrategy', 'dc1' : '1' }};
        """
        session.execute(create_keyspace)
        insert_tracking_table(session, org_name, app_name, schema_as_string, version)
        apply_table(session, org_name, app_name, version, primary_keys, schema)
        return version
    else:
        return prev_version


def list_keyspaces(session: Session, org_name: str) -> dict:
    tables = session.execute(
        f"SELECT * FROM system_schema.tables WHERE keyspace_name = '{org_name}';"
    )
    return {"tables": tables}


def get_data_from_table(
    session: Session, org_name: str, app_name: str, version: int
) -> dict:
    key_space = get_cassandra_key_space_from_org_name(org_name)
    table_name = get_cassandra_table_name_from_app_name(app_name, version)
    full_table_name = f"{key_space}.{table_name}"
    fields = session.execute(f"SELECT * FROM {full_table_name};")
    return {"fields": fields}