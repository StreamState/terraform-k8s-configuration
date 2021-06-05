from typing import List, Dict, Tuple

from streamstate_utils.firestore import (
    get_collection_from_org_name_and_app_name,
)

import json


def get_existing_schema(db, org_name: str, app_name: str) -> Tuple[str, int]:

    doc_stream = (
        db.collection("admin_track")
        .where("organization", "==", org_name)
        .where("appname", "==", app_name)
        .stream()
    )
    for row in doc_stream:
        r = row.to_dict()
        return r["avroschema"], r["version"]

    return "", 0


def _parse_schema(schema: List[Dict[str, str]]):
    for field in schema:
        assert "name" in field
        assert "type" in field
        assert type(field["name"]) == str
        assert type(field["type"]) == str


def set_document_name_version(app_name: str, org_name: str, version: int) -> str:
    return f"{app_name}_{org_name}_{version}"


def set_document_name(app_name: str, org_name: str) -> str:
    return f"{app_name}_{org_name}"


def insert_tracking_table(
    db, org_name: str, app_name: str, avro_schema: str, version: int
):
    document_name_history = set_document_name_version(app_name, org_name, version)
    # creates a new document
    db.collection("admin_track_history").document(document_name_history).set(
        {
            "organization": org_name,
            "avro_schema": avro_schema,
            "version": version,
            "app_name": app_name,
        }
    )
    document_name = set_document_name(app_name, org_name)
    # updates existing document
    db.collection("admin_track").document(document_name).set(
        {
            "organization": org_name,
            "avro_schema": avro_schema,
            "version": version,
            "app_name": app_name,
        }
    )


def _sublist(ls1: List[str], ls2: List[str]) -> bool:
    for x in ls1:
        if x not in ls2:
            return False
    return True


# this doesn't actually create a schema though
def create_schema(
    db,
    org_name: str,
    app_name: str,
    primary_keys: List[str],
    schema: List[Dict[str, str]],  # name: fieldname, type: datatype
):
    # will throw if schema isn't valid
    _parse_schema(schema)
    field_names = [field["name"] for field in schema]
    assert _sublist(primary_keys, field_names)
    prev_schema, prev_version = get_existing_schema(db, org_name, app_name)
    schema_as_string = json.dumps(schema)
    if prev_schema != schema_as_string:
        version = prev_version + 1
        insert_tracking_table(db, org_name, app_name, schema_as_string, version)
        return version
    else:
        return prev_version


# shouldn't use this...just consume from kafka output instead
## if, for example, the data is account_id, count_logins_last_30_days
## with account_id being the primary key, then this would get the most
## recent data for all account_ids
def get_stream_from_table(db, org_name: str, app_name: str, version: int):
    collection = get_collection_from_org_name_and_app_name(org_name, app_name, version)
    # document = get_document_name_from_app_name(app_name, version)

    return db.collection(collection).stream()
