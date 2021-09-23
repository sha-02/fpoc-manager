import netmiko
import re

from netmiko import NetmikoAuthenticationException

import fpoc.fortipoc as fortipoc
from fpoc.devices import FortiGate
from fpoc.exceptions import StopProcessingDevice


def ssh_logon(device: FortiGate):
    """
    Login to FGT via SSH

    :param device:
    :return: ssh handler
    """
    ssh_params = {
        'ip': device.ip,
        'username': device.username,
        'password': device.password,
        'device_type': 'fortinet',
        'port': device.ssh_port,
        # 'verbose': True,
        # 'conn_timeout': 1,
        # 'auth_timeout': 1,
        # 'banner_timeout': 1,
        # 'blocking_timeout': 1,
        # 'timeout': 1,
        # 'session_timeout': 1,
        # 'auto_connect': True,
    }

    # print(netmiko_dict)

    # SSH connection to the FGT
    try:
        ssh = netmiko.ConnectHandler(**ssh_params)
    except NetmikoAuthenticationException:
        print(f'{device.name} : SSH authentication failed. Retrying with empty password.')
        ssh_params['password'] = ''
        ssh = netmiko.ConnectHandler(**ssh_params)

    return ssh


def create_api_admin(device: FortiGate):
    '''
    Create an API admin and retrieve an API key for this admin
    REQUIRES to ALTER the netmiko class for 'fortinet'
    => comment all code in FortinetSSH.session_preparation() method: only keep a 'pass' statement

    :param device:
    :return:
    '''

    ssh = ssh_logon(device)

    # Create API admin
    cli_commands = f'''
    config system api-user
        edit "{device.apiadmin}"
            set accprofile "super_admin"
            set vdom "root"
            config trusthost
                edit 1
                    set ipv4-trusthost {device.mgmt_subnet}
                next
            end
        next
    end    
    '''

    # Create API admin
    output_create_admin = ssh.send_config_set(cli_commands.splitlines())

    # Generate and retrieve the API key for the API admin
    output_generate_apikey = ssh.send_command('exec api-user generate-key adminapi')

    re_token = re.search('New API key:(.+)', output_generate_apikey, re.IGNORECASE)

    if not re_token:    # API key failed to be retrieved => skip this device
        raise StopProcessingDevice(f'device={device.name} : failure to create the API admin or to retrieve '
                                   f'the API key')

    # Update the apikey for this FGT
    device.apikey = re_token.group(1).strip()

    # Store the output of the SSH session (can be useful for debugging)
    device.output = output_create_admin + output_generate_apikey


def retrieve_hostname(device: FortiGate)->str:
    '''

    :param device:
    :return:
    '''
    ssh = ssh_logon(device)

    # Create API admin
    device.output = ssh.send_command('get system status')
    re_token = re.search('Hostname: (.+)', device.output, re.IGNORECASE)

    if not re_token:    # API key failed to be retrieved => skip this device
        raise StopProcessingDevice(f'device={device.name} : failure to retrieve the hostname via SSH')

    # Return the hostname
    return re_token.group(1).strip()