# utils/schema_loader.py

import json

def load_schema_from_file(filepath: str) -> dict:
    """
    Loads and returns JSON schema from a file.
    """
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}
