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
    [_, app_name, table_struct] = sys.argv
    table_schema = marshmallow_dataclass.class_schema(TableStruct)()
    table_info = table_schema.load(json.loads(table_struct))
    cassandra_config = get_cassandra_inputs_from_config_map()
    organization = get_organization_from_config_map()
    # idempotent
    cluster, session = get_cassandra_session(cassandra_config)
    try:
        create_tracking_table(session)
        version = create_schema(
            session,
            organization,
            app_name,
            table_info.primary_keys,
            table_info.output_schema,
        )
        print(version)  # this is needed for Argo to pick this up
    finally:
        cluster.shutdown()


if __name__ == "__main__":
    main()