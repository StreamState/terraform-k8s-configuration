from typing import List
from provision_cassandra import (
    get_cassandra_session,
    create_schema,
    list_keyspaces,
    get_data_from_table,
    create_tracking_table,
)
import marshmallow_dataclass
import sys
from streamstate_utils.cassandra_utils import (
    get_cassandra_inputs_from_config_map,
    get_organization_from_config_map,
)
from streamstate_utils.structs import TableStruct

## need to pass primary keys and avro_schema
## todo, put this in a docker container for argo to run
def main():
    [_, table_struct] = sys.argv

    table_schema = marshmallow_dataclass.class_schema(TableStruct)()
    table_info = output_schema.load(json.loads(table_schema))
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