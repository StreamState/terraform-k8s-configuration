from pydantic import BaseModel
from typing import List, Dict, Union


class Customer(BaseModel):
    name: str
    # description: Optional[str] = None


class Job(BaseModel):
    topics: List[str]
    brokers: List[str]
    namespace: str
    output_topic: str
    project: str
    organization: str
    registry: str
    avro_schema: dict
    version: int
    cassandra_cluster_name: str


class Table(BaseModel):
    organization: str
    # app_name: str
    avro_schema: dict
    primary_keys: List[str]


## TODO! import this from python library
def create_table_name(org_name: str, app_name: str, version: int) -> str:
    return f"{org_name}.{app_name}_{version}"