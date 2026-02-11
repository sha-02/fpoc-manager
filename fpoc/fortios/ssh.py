import re, netmiko, paramiko
import time

from netmiko import NetmikoAuthenticationException
import scp as scp_

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
    password_list = [ssh_params['password'], 'fortinet', '']
    for pwd in password_list:
        ssh_params['password'] = pwd
        try:
            ssh = netmiko.ConnectHandler(**ssh_params)
        except NetmikoAuthenticationException:
            print(f'{device.name} : SSH authentication failed with password "{pwd}". Trying with next password...')
            continue
            # ssh = netmiko.ConnectHandler(**ssh_params)
        else:
            print(f'{device.name} : Successful SSH authentication with password "{pwd}"')
            break

    return ssh


# Used as backup solution if there is a failure of the API authentication based on username-password
def create_api_admin(device: FortiGate):
    """
    Create an API admin and retrieve an API key for this admin
    :param device:
    :return:
    """
    def commands_with_password(ssh, password: str, cmd_list: list):
        output = ''
        for cmd in cmd_list:
            output += ssh.send_command_timing(cmd, strip_prompt=False, strip_command=False)
            # Check if FortiOS is asking for password
            if "password" in output.lower():
                output += ssh.send_command_timing(password, strip_prompt=False, strip_command=False)

        return output

    ssh = ssh_logon(device)
    device.output = ''

    # Check if there is an API admin already configured on this device
    device.output += ssh.send_command(f'get sys api-user | grep "name: {device.apiadmin}"')
    if device.output.strip() != f'name: {device.apiadmin}':  # API admin is not configured on the device
        # Create API admin (admin password requested as of 7.6.4)
        cli_commands = f'''
config system api-user
edit "{device.apiadmin}"
    set accprofile super_admin
end
'''
        print(f'{device.name} : Create API admin')
        device.output += commands_with_password(ssh, device.password, cli_commands.splitlines())

    time.sleep(1)

    # Generate and retrieve the API key for the API admin (admin password requested as of 7.6.4)
    print(f'{device.name} : Generate API key')

    output_api = commands_with_password(ssh, device.password, [f'exec api-user generate-key {device.apiadmin}'])
    device.output += output_api

    re_token = re.search('New API key:(.+)', output_api, re.IGNORECASE)

    if not re_token:  # API key failed to be retrieved => skip this device
        raise StopProcessingDevice(f'device={device.name} : failure to retrieve the API key: <pre>{device.output}</pre>')

    # Update the apikey for this FGT
    device.apikey = re_token.group(1).strip()


def upload_firmware(device: FortiGate, firmware: str):
    """
    Update (upgrade or downgrade) the firmware of this FGT

    :param device:
    :param firmware: filename of the firmware to be uploaded to the FGT
    :return:
    """
    ssh = paramiko.SSHClient()
    # ssh.load_system_host_keys()   # Do not load system host jeys otherwise it can trigger paramiko.ssh_exception.BadHostKeyException
    ssh.set_missing_host_key_policy(paramiko.WarningPolicy())   # Accept unknown server key, simply log a warning
    ssh.connect(hostname=device.ip, username=device.username, password=device.password, port=device.ssh_port)

    scp = scp_.SCPClient(ssh.get_transport())   # SCPCLient takes a paramiko transport as an argument

    # Upload firmware
    scp.put(remote_path='fgt-image', files=firmware)

    # close connections
    scp.close(); ssh.close()

# Legacy functions for old FOS versions (< 7.0) #####################

def retrieve_hostname(device: FortiGate) -> str:
    """

    :param device:
    :return:
    """
    ssh = ssh_logon(device)

    device.output = ssh.send_command('get system status')
    re_token = re.search('Hostname: (.+)', device.output, re.IGNORECASE)

    if not re_token:  # failed to retrieve hostname => skip this device
        raise StopProcessingDevice(f'device={device.name} : failure to retrieve the hostname via SSH')

    # Return the hostname
    return re_token.group(1).strip()


def is_running_ha(device: FortiGate) -> bool:
    """

    :param device:
    :return:
    """
    ssh = ssh_logon(device)

    device.output = ssh.send_command('get system status')
    re_token = re.search('Current HA mode: (.+)', device.output, re.IGNORECASE)

    if not re_token:  # failed to retrieve HA status => skip this device
        raise StopProcessingDevice(f'device={device.name} : failure to retrieve the HA status via SSH')

    # Return True if HA mode is not 'standalone', return False if HA mode is 'standalone'
    return re_token.group(1).strip() != 'standalone'
