from fpoc.json import json_to_dict
from config.settings import BASE_DIR


def fortipoc_instances() -> dict:
    """
    Load the FortiPoC VM dictionary from JSON file
    :return: dict of FortiPoC VMs
    """
    return json_to_dict(f'{BASE_DIR}/fpoc/fortipoc_instances.json')