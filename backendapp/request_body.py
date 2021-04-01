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
    cassandra_cluster_name: str


class Table(BaseModel):
    namespace: str
    app_name: str
    db_schema: Dict[str, Union[Dict[str, str], List[str]]]  # or use avro?
