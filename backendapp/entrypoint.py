from typing import List
from provision_cassandra import (
    get_cassandra_session,
    create_schema,
    create_tracking_table,
)
import marshmallow_dataclass
import sys
from streamstate_utils.cassandra_utils import (
    get_cassandra_inputs_from_config_map,
    get_organization_from_config_map,
)
from streamstate_utils.structs import TableStruct
import json


def main():
    [_, table_struct] = sys.argv
    print(table_struct)
    table_schema = marshmallow_dataclass.class_schema(TableStruct)()
    table_info = table_schema.load(json.loads(table_struct))
    cassandra_config = get_cassandra_inputs_from_config_map()
    organization = get_organization_from_config_map()
    # idempotent
    session = get_cassandra_session(cassandra_config)
    create_tracking_table(session)
    # checks validity of avro_schema
    version = create_schema(
        session,
        organization,
        table_info.primary_keys,
        table_info.output_schema,
    )
    return version


if __name__ == "__main__":
    main()