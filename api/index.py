from typing import List, Callable, Optional, Dict, Union

from fastapi import FastAPI, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from streamstate_utils.structs import (
    InputStruct,
    KafkaStruct,
    OutputStruct,
    TableStruct,
)


app = FastAPI()
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

# Configs can be set in Configuration class directly or using helper utility
config.load_incluster_config()
V1 = client.CoreV1Api()
CUSTOM_OBJECT = client.CustomObjectsApi()
ORGANIZATION = get_organization_from_config_map()
PROJECT_ID = get_project_from_config_map()
DB = open_firestore_connection(PROJECT_ID)
NAMESPACE = os.getenv("NAMESPACE", "")
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


def check_auth_head(authorization: str) -> bool:
    return authorization.startswith("Bearer ")


def check_auth(authorization: str, actual_token: str) -> bool:
    token = authorization.replace("Bearer ", "")
    return token == actual_token


def get_write_token() -> str:
    return os.getenv("WRITE_TOKEN", "")


def get_read_token() -> str:
    return os.getenv("READ_TOKEN", "")


def auth_checker(authorization: Optional[str], get_token: Callable[[], str]):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header required")

    if not check_auth_head(authorization):
        raise HTTPException(status_code=401, detail="Malformed authorization header")

    actual_token = get_token()
    if not check_auth(authorization, actual_token):
        raise HTTPException(status_code=401, detail="Incorrect token")


@app.post("/api/{app_name}/stop")
def stop_spark_job(app_name: str, authorization: Optional[str] = Header(None)):
    auth_checker(authorization, get_write_token)
    try:
        api_response = CUSTOM_OBJECT.delete_namespaced_custom_object(
            "sparkoperator.k8s.io",
            "v1beta2",
            NAMESPACE,
            "sparkapplications",
            app_name,
            body=client.V1DeleteOptions(),
        )
        return api_response
    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=e.body)


@app.get("/api/{app_name}/features/{version}")
def read_feature(
    app_name: str,
    version: int,
    filter: List[str],
    authorization: Optional[str] = Header(None),
):
    auth_checker(authorization, get_read_token)
    return get_latest_record(DB, ORGANIZATION, app_name, version, filter)


class ApiDeploy(BaseModel):
    pythoncode: str
    inputs: List[InputStruct]
    assertions: List[Dict[str, Union[str, float, int, bool]]]
    kafka: KafkaStruct
    outputs: OutputStruct
    table: TableStruct


## this is a dummy endpoint, to
## add docs to the argo webhook
## endpoint.  This never gets
## called because our ingress
## redirects api/deploy to argo
@app.post("/api/deploy")
def dummy_deploy(
    body: ApiDeploy,
    authorization: Optional[str] = Header(None),
):
    return "Success"
