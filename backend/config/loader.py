import json
from pathlib import Path


def load_config(path: str = None) -> dict:
    if path is None:
        path = Path(__file__).parent / "config.json"
    with open(path, "r") as f:
        return json.load(f)
