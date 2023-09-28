from netmiko import NetmikoAuthenticationException
from django.core.handlers.wsgi import WSGIRequest
from django.template import loader
import os.path

# import fpoc.ssh
from config.settings import PATH_FPOC_TEMPLATES
from fpoc import TypePoC, VyOS

import netmiko, paramiko


def deploy(request: WSGIRequest, poc: TypePoC, device: VyOS):
    """
    Render the configuration (Django template) and deploy it

    :param request:
    :param poc:
    :param device:
    :return:
    """

    # Render the VyOS config
    # - use the per-POC VyOS template if one exists
    # - otherwise use the generic VyOS template

    template_name = f'fpoc/{poc.__class__.__name__}/poc{poc.id:02}/{device.template_filename}'
    if not os.path.isfile(os.path.dirname(PATH_FPOC_TEMPLATES)+'/'+template_name):
        template_name = f'fpoc/{device.template_filename}'

    print(f'{device.name} : Rendering VyOS template {template_name}')

    # No need to pass the 'request' (which adds CSRF tokens) since this is a rendering for Linux CLI settings
    device.config = loader.render_to_string(template_name, device.template_context, using='jinja2')

    # Deploy the config
    #
    if request.POST.get('previewOnly'):  # Only preview of the config is requested, no deployment needed
        return None  # No more processing needed for this FGT

    # Run the CLI settings on the LXC
    ssh_params = {
        'device_type': 'vyos',
        'ip': device.ip,
        'username': device.username,
        'password': device.password,
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

    # Set specific SSH KexAlgorithms and HostKeyAlgorithms required for our old VyOS
    # paramiko.Transport._preferred_kex = ('diffie-hellman-group1-sha1')  # SSH KexAlgorithms
    # paramiko.Transport._preferred_keys = ('ssh-rsa')  # SSH HostKeyAlgorithms

    ssh = netmiko.ConnectHandler(**ssh_params)

    password_list = [device.password, 'nsefortinet', 'fortinet']
    for pwd in password_list:
        ssh_params['password'] = pwd
        try:
            device.output = ssh.send_config_set(device.config.splitlines(), exit_config_mode=False)
        except NetmikoAuthenticationException:
            print(f'{device.name} : SSH authentication failed with password "{pwd}". Trying with next password...')
            continue
        else:
            print(f'{device.name} : Successful SSH authentication with password "{pwd}"')
            print(device.output)
            break

    print(ssh.commit())
    ssh.exit_config_mode()
    print(ssh.send_command("sh ip route static"))

    ssh.disconnect()
