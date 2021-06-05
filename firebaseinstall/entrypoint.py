from provision_firestore import (
    create_schema,
)
import sys

from streamstate_utils.k8s_utils import (
    get_organization_from_config_map,
    get_project_from_config_map,
)

from streamstate_utils.firestore import open_firestore_connection
from streamstate_utils.structs import TableStruct
import json


def main():
    [_, app_name, table_struct] = sys.argv
    table_info = TableStruct(**json.loads(table_struct))
    organization = get_organization_from_config_map()
    project_id = get_project_from_config_map()
    db = open_firestore_connection(project_id)

    version = create_schema(
        db,
        organization,
        app_name,
        table_info.primary_keys,
        table_info.output_schema,
    )
    print(version)  # this is needed for Argo to pick this up


if __name__ == "__main__":
    main()
