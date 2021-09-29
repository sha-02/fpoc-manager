import io
import re
from random import randrange

import netmiko
import paramiko
import scp as scp_

# start = time.perf_counter()
# print("Time: ", time.perf_counter()-start)

fortigate = {
    'ip': '10.5.58.151',
    'username': 'admin',
    'password': 'fortinet',
    'port': 10101,
}


def netmiko_kwargs(fgt):
    """
    """
    return {**fgt,
            'device_type': 'fortinet',
            # 'verbose': True,
            # 'conn_timeout': 1,
            # 'auth_timeout': 1,
            # 'banner_timeout': 1,
            # 'blocking_timeout': 1,
            # 'timeout': 1,
            # 'session_timeout': 1,
            # 'auto_connect': True,
            }


def paramiko_kwargs(fgt):
    """
    """
    dic = {**fgt, 'hostname': fgt['ip']}
    del (dic['ip'])
    return dic


def test_ssh(fgt):
    ssh = netmiko.ConnectHandler(**netmiko_kwargs(fgt))

    output = ssh.send_command('sh system global')
    print(output)

    commands = ['config system global', f'set admintimeout {randrange(100, 480)}', 'end']
    output = ssh.send_config_set(commands)
    print(output)

    output = ssh.send_command('sh system global')
    print(output)

    ssh.disconnect()


def test_scp(fgt):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
    ssh.connect(**paramiko_kwargs(fgt))

    # SCPCLient takes a paramiko transport as an argument
    scp = scp_.SCPClient(ssh.get_transport())

    # retrieve config from FGT
    scp.get(remote_path='sys_config', local_path='./x_bootstrap_config.txt')

    # # generate in-memory file-like object
    # fl = io.BytesIO()
    # fl.write(b'test')
    # fl.seek(0)
    # # upload it directly from memory
    # scp.putfo(fl, '/tmp/test.txt')
    # close file handler
    # fl.close()

    # close connection
    scp.close()
    ssh.close()


def retrieve_bootstrap_config(fgt):
    """
    """
    ssh = netmiko.ConnectHandler(**netmiko_kwargs(fgt))

    # If the prompt contains a hostname of the form "FGVM<12-digits>" then this is a FortiPoC bootstrap config
    if not re.match('FGVM\d{12,12}', ssh.find_prompt()):
        ssh.disconnect()
        return ''   # return empty string if the FGT is not running a bootstrap config

    # verify that scp is enabled in system.global; if not, enable it
    if 'set admin-scp enable' not in ssh.send_command('sh system global'):
        commands = ['config system global', 'set admin-scp enable', 'end']
        print(ssh.send_config_set(commands))

    ssh.disconnect()

    # FGT has bootstrap config, retrieve it via SCP
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
    ssh.connect(**paramiko_kwargs(fgt))

    scp = scp_.SCPClient(ssh.get_transport())   # SCPCLient takes a paramiko transport as an argument

    # retrieve the bootstrap config from FGT
    filename = './x_bootstrap_config.txt'
    scp.get(remote_path='sys_config', local_path=filename)

    # load the bootstrap config in a string
    with open(filename) as f:
        filecontent = f.read()

    ssh.close()
    scp.close()

    # return the string containing the bootstrap config
    return filecontent


# test_ssh(fortigate)
# test_scp(fortigate)

bootstrap_config = retrieve_bootstrap_config(fortigate)
print(bootstrap_config)
