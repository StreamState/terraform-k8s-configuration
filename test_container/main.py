import sys

sys.path.append("/opt/spark/work-dir/")
from dev_app import dev_from_file
import json
from streamstate_utils.structs import FileStruct, InputStruct

if __name__ == "__main__":
    [
        _,
        app_name,  #
        file_struct,
        input_struct,
    ] = sys.argv
    file_info = FileStruct(**json.loads(file_struct))
    input_info = [InputStruct(**v) for v in json.loads(input_struct)]
    dev_from_file(
        app_name,
        file_info.max_file_age,
        input_info,
    )
