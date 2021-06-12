from typing import List, Dict, Tuple

from streamstate_utils.firestore import (
    get_collection_from_org_name_and_app_name,
)

import json


def get_existing_schema(db, org_name: str, app_name: str) -> int:
    document_name = set_document_name(app_name, org_name)
    doc = db.collection("admin_track").document(document_name).get()
    if doc.exists:
        return doc.to_dict()["code_version"]
    else:
        return 0


def _parse_schema(schema: List[Dict[str, str]]):
    for field in schema:
        assert "name" in field
        assert "type" in field
        assert type(field["name"]) == str
        assert type(field["type"]) == str


def set_document_name_version(
    app_name: str, org_name: str, schema_version: int, code_version: int
) -> str:
    return f"{app_name}_{org_name}_{schema_version}_{code_version}"


def set_document_name(app_name: str, org_name: str) -> str:
    return f"{app_name}_{org_name}"


def insert_tracking_table(
    db,
    org_name: str,
    app_name: str,
    avro_schema: str,
    code_version: int,
):
    document_name_history = set_document_name_version(app_name, org_name, code_version)
    # creates a new document
    db.collection("admin_track_history").document(document_name_history).set(
        {
            "organization": org_name,
            "avro_schema": avro_schema,
            "code_version": code_version,
            "app_name": app_name,
        }
    )

    document_name = set_document_name(app_name, org_name)
    # updates existing document
    db.collection("admin_track").document(document_name).set(
        {
            "organization": org_name,
            "avro_schema": avro_schema,
            "code_version": code_version,
            "app_name": app_name,
        }
    )


def _sublist(ls1: List[str], ls2: List[str]) -> bool:
    for x in ls1:
        if x not in ls2:
            return False
    return True


# this doesn't actually create a schema though
def version_code_and_schema(
    db,
    org_name: str,
    app_name: str,
    primary_keys: List[str],
    schema: List[Dict[str, str]],  # name: fieldname, type: datatype
) -> int:
    # will throw if schema isn't valid
    _parse_schema(schema)
    field_names = [field["name"] for field in schema]
    assert _sublist(primary_keys, field_names)
    prev_code_version = get_existing_schema(db, org_name, app_name)
    schema_as_string = json.dumps(schema)

    code_version = prev_code_version + 1
    insert_tracking_table(db, org_name, app_name, schema_as_string, code_version)
    return code_version
    # else:
    #    return prev_version


# shouldn't use this...just consume from kafka output instead
## if, for example, the data is account_id, count_logins_last_30_days
## with account_id being the primary key, then this would get the most
## recent data for all account_ids
def get_stream_from_table(db, org_name: str, app_name: str, version: int):
    collection = get_collection_from_org_name_and_app_name(org_name, app_name, version)
    # document = get_document_name_from_app_name(app_name, version)

    return db.collection(collection).stream()
