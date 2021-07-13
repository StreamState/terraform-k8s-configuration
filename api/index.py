from typing import List, Optional, Dict, Union, Tuple

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from streamstate_utils.structs import (
    FileStruct,
    InputStruct,
    KafkaStruct,
    OutputStruct,
    TableStruct,
)

from utils import group_applications


app = FastAPI(openapi_url="/docs/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="https://.*\.streamstate\.org",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from streamstate_utils.firestore import (
    get_collection_from_org_name_and_app_name,
    get_document_name_from_version_and_keys,
    open_firestore_connection,
)
from streamstate_utils.k8s_utils import (
    get_organization_from_config_map,
    get_project_from_config_map,
)


from kubernetes import client, config
from kubernetes.client.rest import ApiException
import base64

# Configs can be set in Configuration class directly or using helper utility
config.load_incluster_config()
V1 = client.CoreV1Api()
CUSTOM_OBJECT = client.CustomObjectsApi()
ORGANIZATION = get_organization_from_config_map()
PROJECT_ID = get_project_from_config_map()
DB = open_firestore_connection(PROJECT_ID)
NAMESPACE = os.getenv("NAMESPACE", "")
SERVICE_NAMESPACE = os.getenv("SERVICE_NAMESPACE", "")
## if, for example, the data is account_id, count_logins_last_30_days
## with account_id being the primary key, then this would get the most
## recent data for this account_id
def get_latest_record(
    db, org_name: str, app_name: str, version: int, key_values: List[str]
) -> dict:
    """
    Gets latest record by key

    Attributes:
    db: instance of firestore client
    org_name: name of organization
    app_name: name of app
    version: schema version
    key_values: the values of the primary key columns.
    Must be in the same order as on write
    """
    collection = get_collection_from_org_name_and_app_name(org_name, app_name)
    document = get_document_name_from_version_and_keys(key_values, version)

    return db.collection(collection).document(document).get().to_dict()


def create_new_secret(
    secret_name: str, namespace: str, secrets: List[Tuple[str, str]]
) -> str:  # secret_text: str, key_names: List[str]) -> str:
    data = {
        key_name: base64.b64encode(secret_text.encode()).decode("utf-8")
        for key_name, secret_text in secrets
    }
    body = client.V1Secret()
    body.api_version = "v1"
    body.data = data
    body.kind = "Secret"
    body.metadata = {"name": secret_name, "namespace": namespace}
    return V1.patch_namespaced_secret(secret_name, namespace, body)


@app.get("/api/applications")
def applications():
    try:
        response = CUSTOM_OBJECT.list_namespaced_custom_object(
            "sparkoperator.k8s.io", "v1beta2", NAMESPACE, "sparkapplications"
        )
        return group_applications(response["items"])
    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=e.body)


@app.post("/api/{app_name}/stop")
def stop_spark_job(app_name: str):
    try:
        response = CUSTOM_OBJECT.list_namespaced_custom_object(
            "sparkoperator.k8s.io",
            "v1beta2",
            NAMESPACE,
            "sparkapplications",
            label_selector=f"app={app_name}",
        )
        result = []
        for application in response["items"]:
            api_response = CUSTOM_OBJECT.delete_namespaced_custom_object(
                "sparkoperator.k8s.io",
                "v1beta2",
                NAMESPACE,
                "sparkapplications",
                application["metadata"]["name"],
                body=client.V1DeleteOptions(),
            )
            result.append(api_response)
        return result
    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=e.body)


@app.get("/api/{app_name}/features/{code_version}")
def read_feature(
    app_name: str,
    code_version: int,
    filter: Optional[List[str]] = Query(None),
):
    if filter is None:
        raise HTTPException(status_code=400, detail="Query parameter filter required")
    return get_latest_record(DB, ORGANIZATION, app_name, code_version, filter)


class ApiReplay(BaseModel):
    inputs: List[InputStruct]
    kafka: KafkaStruct
    outputs: OutputStruct
    table: TableStruct
    fileinfo: FileStruct
    appname: str
    code_version: int

    class Config:
        schema_extra = {
            "example": {
                "inputs": [
                    {
                        "topic": "topic1",
                        "sample": [{"field1": "somevalue"}],
                        "topic_schema": [{"name": "field1", "type": "string"}],
                    }
                ],
                "kafka": {"brokers": "broker1,broker2"},
                "outputs": {"mode": "append", "processing_time": "2 seconds"},
                "fileinfo": {"max_file_age": "2d"},
                "table": {
                    "primary_keys": ["field1"],
                    "output_schema": [{"name": "field1", "type": "string"}],
                },
                "appname": "mytestapp",
                "code_version": 1,
            }
        }


class ApiDeploy(BaseModel):
    pythoncode: str
    inputs: List[InputStruct]
    assertions: List[Dict[str, Union[str, float, int, bool]]]
    kafka: KafkaStruct
    outputs: OutputStruct
    table: TableStruct
    fileinfo: FileStruct
    appname: str

    class Config:
        schema_extra = {
            "example": {
                "pythoncode": "ZnJvbSB0eXBpbmcgaW1wb3J0IExpc3QKZnJvbSBweXNwYXJrLnNxbCBpbXBvcnQgRGF0YUZyYW1lCgoKZGVmIHByb2Nlc3MoZGZzOiBMaXN0W0RhdGFGcmFtZV0pIC0+IERhdGFGcmFtZToKICAgIHJldHVybiBkZnNbMF0K",
                "inputs": [
                    {
                        "topic": "topic1",
                        "sample": [{"field1": "somevalue"}],
                        "topic_schema": [{"name": "field1", "type": "string"}],
                    }
                ],
                "assertions": [{"field1": "somevalue"}],
                "kafka": {"brokers": "broker1,broker2"},
                "outputs": {"mode": "append", "processing_time": "2 seconds"},
                "table": {
                    "primary_keys": ["field1"],
                    "output_schema": [{"name": "field1", "type": "string"}],
                },
                "appname": "mytestapp",
            }
        }


## this is a dummy endpoint, to
## add docs to the argo webhook
## endpoint.  This never gets
## called because our ingress
## redirects api/deploy to argo
@app.post("/api/deploy")
def create_spark_streaming_replay_job(body: ApiDeploy):
    return "success"


## this is a dummy endpoint, to
## add docs to the argo webhook
## endpoint.  This never gets
## called because our ingress
## redirects api/deploy to argo
@app.post("/api/replay")
def create_spark_streaming_job(
    body: ApiReplay,
):
    return "success"
