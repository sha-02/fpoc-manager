import json
from jsmin import jsmin

from fpoc import AbortDeployment
from config.settings import BASE_DIR


def json_to_dict(filepath: str) -> dict:
    """
    Load dictionary from JSON file
    :return: python dict
    """
    try:
        with open(filepath, "r") as f:
            minified = jsmin(f.read())  # jsmin is used to remove C++ style comments (//) from JSON code
            return json.loads(minified)

    except FileNotFoundError:
        print(f'File not found: {filepath}')
        raise AbortDeployment