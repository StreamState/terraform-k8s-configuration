from pydantic import BaseModel
from typing import List, Dict, Union


class Customer(BaseModel):
    name: str
    # description: Optional[str] = None


class Job(BaseModel):
    topics: List[str]
    brokers: List[str]
    namespace: str
    cassandraIp: str
    cassandraPort: str


class Table(BaseModel):
    namespace: str
    app_name: str
    db_schema: Dict[str, Union[Dict[str, str], List[str]]]
