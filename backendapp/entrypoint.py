from typing import List
from provision_cassandra import (
    get_cassandra_session,
    create_schema,
    list_keyspaces,
    get_data_from_table,
    create_tracking_table,
)
import os
from streamstate_utils.utils import (
    get_cassandra_inputs_from_config_map,
    get_organization_from_config_map,
)

## need to pass primary keys and avro_schema
def main():
    cassandra_config = get_cassandra_inputs_from_config_map()
    organization = get_organization_from_config_map()
    # idempotent
    session = get_cassandra_session(cassandra_config)
    create_tracking_table(session)
    # checks validity of avro_schema
    version = create_schema(
        session,
        organization,
        table.primary_keys,
        table.avro_schema,
    )
    return version


if __name__ == "__main__":
    main()