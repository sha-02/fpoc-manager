from fpoc.json import json_to_dict
from config.settings import BASE_DIR


def fortipoc_instances() -> dict:
    """
    Load the Studio VM dictionary from JSON file
    :return: dict of VM instances
    """
    return json_to_dict(f'{BASE_DIR}/fpoc/studio_instances.json')