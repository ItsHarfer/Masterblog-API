import json


def load_config(path: str = "config/config.json") -> dict:
    with open(path, "r") as f:
        return json.load(f)
