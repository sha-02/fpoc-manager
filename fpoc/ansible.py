import yaml
import fpoc
from config.settings import PATH_FPOC_CONFIG_SAVE


def poweron_devices(devices: list, host: str, admin: str, pwd: str) -> tuple:
    inventory = 'FortiPoC ansible_host=' + host + ' ansible_user=' + admin + ' ansible_password=' + pwd

    playbook = [
      {
        "hosts": "FortiPoC",
        "gather_facts": False,
        "tasks": [
          {
            "name": "poweron devices",
            "raw": "poc device poweron {{ item }}",
            "loop": devices
          }
        ]
      }
    ]

    inventory_file = f'{PATH_FPOC_CONFIG_SAVE}/ansible_inventory.txt'
    with open(inventory_file, 'w') as fd:
        fd.write(inventory)

    playbook_file = f'{PATH_FPOC_CONFIG_SAVE}/ansible_playbook.yml'
    with open(playbook_file, 'w') as fd:
        yaml.dump(playbook, fd, indent=4)

    return fpoc.syscall_realtime(f'ansible-playbook -i {inventory_file} {playbook_file}')

