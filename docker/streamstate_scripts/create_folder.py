from streamstate_utils.gcs_create_folder import create_gcs_folders
from streamstate_utils.structs import InputStruct
import sys
import json

if __name__ == "__main__":
    [_, app_name, bucket_name, input_struct] = sys.argv
    input_info = [InputStruct(**v) for v in json.loads(input_struct)]
    create_gcs_folders(bucket_name, app_name, input_info)
