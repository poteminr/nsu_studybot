import json


def import_private_keys(json_path: str, key_name: str) -> str:
    with open(json_path) as f:
        keys = json.load(f)

    return keys[key_name]
