import json
from pathlib import Path
import warnings


def load_config(path: str = None) -> dict:
    if path is None:
        path = Path(__file__).parent / "config.json"
    with open(path, "r") as f:
        return json.load(f)


def apply_runtime_config():
    # Suppress in-memory warning from flask_limiter in dev
    warnings.filterwarnings("ignore", category=UserWarning, module="flask_limiter")
