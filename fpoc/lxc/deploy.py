from netmiko import NetmikoAuthenticationException
from django.core.handlers.wsgi import WSGIRequest
from django.template import loader
import os.path

import fpoc.ssh
from config.settings import PATH_FPOC_TEMPLATES
from fpoc import TypePoC, LXC


def deploy(request: WSGIRequest, poc: TypePoC, device: LXC):
    """
    Render the configuration (Django template) and deploy it

    :param request:
    :param poc:
    :param device:
    :return:
    """

    # Render the LXC config
    # - use the per-POC LXC template if one exists
    # - otherwise use the generic LXC template

    template_name = f'fpoc/{poc.__class__.__name__}/poc{poc.id:02}/{device.template_filename}'
    if not os.path.isfile(os.path.dirname(PATH_FPOC_TEMPLATES)+'/'+template_name):
        template_name = f'fpoc/{device.template_filename}'

    print(f'{device.name} : Rendering LXC template {template_name}')

    # No need to pass the 'request' (which adds CSRF tokens) since this is a rendering for Linux CLI settings
    device.config = loader.render_to_string(template_name, device.template_context, using='jinja2')
    # print(cli_settings)

    # Save this CLI configuration script to disk
    # filename = f'{BASE_DIR}/templates/{template_base_path}/__{device.name}__.conf'
    # with open(filename, 'w') as f:
    #     f.write(device.config)

    # print(f'CLI configuration script saved to {filename}')

    # Deploy the config
    #
    if request.POST.get('previewOnly'):  # Only preview of the config is requested, no deployment needed
        return None  # No more processing needed for this FGT

    # Run the CLI settings on the LXC
    ssh_params = {
        'device_type': 'linux',
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

    password_list = [device.password, 'fortinet', '']
    for pwd in password_list:
        ssh_params['password'] = pwd
        try:
            device.output = fpoc.ssh.send_config_set(ssh_params, device.config.splitlines())
        except NetmikoAuthenticationException:
            print(f'{device.name} : SSH authentication failed with password "{pwd}". Trying with next password...')
            continue
        else:
            print(f'{device.name} : Successful SSH authentication with password "{pwd}"')
            print(device.output)
            break
