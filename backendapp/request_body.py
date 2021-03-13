from pydantic import BaseModel
from typing import List


class Customer(BaseModel):
    name: str
    # description: Optional[str] = None


class Job(BaseModel):
    topics: List[str]
    brokers: List[str]
    namespace: str
    cassandraIp: str
    cassandraPassword: str