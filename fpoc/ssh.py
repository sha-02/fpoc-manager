import netmiko


def send_config_set(ssh_params: dict, commands: list):
    """
    Execute a set of commands via SSH

    :param ssh_params:
    :param commands:
    :return:
    """
    ssh = netmiko.ConnectHandler(**ssh_params)
    output = ssh.send_config_set(commands)
    ssh.disconnect()
    return output
