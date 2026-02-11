import base64
import json
import requests
import urllib3
import sys, os

import fpoc.fortios as fortios
from fpoc import FortiGate
from fpoc import StopProcessingDevice, RetryProcessingDevice

# FGT use self-signed certificate => De-activate the TLS warnings.
urllib3.disable_warnings()


#
# API authentication based on username-password instead of API token
# https://fndn.fortinet.net/index.php?/fortiapi/1-fortios/596/
#
# and some additional info in (POST request is a MUST):
# https://mantis.fortinet.com/bug_view_page.php?bug_id=0712590
#
# Mantis in which the new login API allowing password-based authentication
# and optional trusted-host for API admin was introduced in 6.4.2:
# https://mantis.fortinet.com/bug_view_page.php?bug_id=0647762
#

# As of 7.6.1/7.4.5 (1058092), use of REST API keys in the URL (as a query parameter) is controlled by a CLI setting
# (rest-api-key-url-query in system.global) which is disabled by default
# This FOS API library passes the API key (access_token) in the header instead of URL

def retrieve_access_token(device: FortiGate) -> str:
    """
    Retrieve an access_token using APIv2 admin/password authentication without the need to create an API admin (api-user) via SSH
    In 7.6.4, 'secretkey' parameter was replaced by 'password' so I included both in the API call
    7.6.4 no longer provides a 'session_key': the official auth method is with the use of an API user (1202007).
    0938055 ( /api/v2/authentication removed from FNDN ). NFR 1209507 was raised anyway.
    As of 7.6.4, the session key seems to be in the Set-Cookie HTTP header in variable with name starting with "session_key"
    I tried to extract this session key and use it for subsequent requests but it failed with "status_code=401 reason=Unauthorized"
    So, I'm deprecating the use of this API for the time being

    :param device:
    :return:
    """

    def extract_session_key(data):
        # Split the input string by commas to separate the variables
        if data is None:
            return None
        parts = data.split(', ')
        for part in parts:
            # Further split by '=' to separate the variable name and its value
            if part.startswith('session_key'):
                name_value = part.split('=')
                if len(name_value) > 1:
                    return name_value[1].split(';')[0]  # Return the value before any semicolon
        return None  # Return None if not found

    url = f"https://{device.ip}:{device.https_port}/api/v2/authentication"

    payload = {'username': device.username, 'secretkey': device.password, 'password': device.password,
               'ack_post_disclaimer': True, 'request_key': True }
    response = requests.request("POST", url, headers={'accept': 'application/json'}, data=json.dumps(payload),
                                verify=False)

    if response.status_code != 200: # API access failed
        raise RetryProcessingDevice(f'{device.name} : failure to retrieve an access_token using APIv2 admin/password authentication'
                                   f'\nstatus_code={response.status_code} reason={response.reason} \ntext={response.text}\n')

    res1 = response.json().get('session_key')    # FOS up to 7.6.3
    res2 = extract_session_key( dict(response.headers).get('Set-Cookie') ) # FOS 7.6.4+ : session_key in Set-Cookie HTTP Header
    if res1 is None and res2 is None:
        raise RetryProcessingDevice(f'{device.name} : failure to retrieve access_token. response=', response.text, '\n')

    return res1 if res1 is not None else res2


def configure(device: FortiGate, path: str, payload: dict, error_msg:str , error_action=RetryProcessingDevice):
    """
    Configure a FortiOS item
    """
    url = f"https://{device.ip}:{device.https_port}/api/v2/cmdb{path}"

    response = requests.request("PUT", url,
                                headers={'accept': 'application/json', 'authorization': 'Bearer '+device.apikey},
                                data=json.dumps(payload),
                                verify=False)

    if response.status_code != 200: # API access failed
        raise error_action(f'{device.name} : {error_msg}'
                                    f'\nstatus_code={response.status_code} '
                                    f'reason={response.reason} \ntext={response.text}\n')


def show(device: FortiGate, path: str, error_msg:str, error_action=RetryProcessingDevice)->requests.Response:
    """
    Get a FortiOS configuration item
    """
    url = f"https://{device.ip}:{device.https_port}/api/v2/monitor{path}"

    response = requests.request("GET", url,
                                headers={'accept': 'application/json', 'authorization': 'Bearer '+device.apikey},
                                verify=False)

    if response.status_code != 200: # API access failed
        raise error_action(f'{device.name} : {error_msg}'
                                    f'\nstatus_code={response.status_code} '
                                    f'reason={response.reason} \ntext={response.text}\n')

    return response


def retrieve_hostname(device: FortiGate) -> str:
    """
    Retrieve the hostname of the FGT

    :param device:
    :return:
    """
    response = show(device, path='/system/status', error_msg='failure to retrieve FGT hostname')
    res = response.json().get('results', {}).get('hostname')
    if res is None:
        raise RetryProcessingDevice(f'{device.name} : failure to retrieve hostname. response=', response.text, '\n')

    return res


def is_running_ha(device: FortiGate) -> bool:
    """
    Retrieve the HA peers of the FGT

    :param device:
    :return:
    """
    response = show(device, path='/system/ha-peer', error_msg='failure to retrieve HA status of FGT')
    return bool(len(response.json().get('results', [])))   # 'results' is a list of all HA peers. List is empty if no HA.


def change_hostname(device: FortiGate, hostname: str):
    """
    Change the Hostname on the FGT

    :param device:
    :param hostname:
    :return:
    """
    configure(device, path='/system/global', payload={'hostname': hostname}, error_msg='failure during update of firmware')


def enable_vdom_mode(device: FortiGate):
    """
    Enable the equivalent of 'set vdom-mode multi-vdom' via API

    :param device:
    :return:
    """
    configure(device, path='/system/global', payload={'vdom-mode': 'multi-vdom'}, error_msg='failure to enable VDOMs')


def retrieve_vdom_mode(device: FortiGate) -> str:
    """
    Check the value of 'set vdom-mode {no-vdom|multi-vdom}' via API

    :param device:
    :return:
    """
    response = show(device, path='/system/global', error_msg='failure to check the vdom-mode')
    res = response.json().get('results', {}).get('vdom-mode')
    if res is None:
        raise RetryProcessingDevice(f'{device.name} : failure to check the vdom-mode. response=', response.text, '\n')

    return res


def retrieve_fos_version(device: FortiGate) -> str:
    """
    Get the FOS version running on the FGT and update device.fos_version accordingly

    :param device:
    :return:
    """
    response = show(device, path='/system/status', error_msg='failure to retrieve FortiOS version')
    res = response.json().get('version')
    if res is None:
        raise RetryProcessingDevice(f'{device.name} : failure to retrieve FortiOS version. response=', response.text, '\n')

    return res[1:]  # string returned is for e.g. "v6.4.4", so need to only keep "6.4.4"


def upload_firmware(device: FortiGate, firmware: str):
    """
    Update (upgrade or downgrade) the firmware of this FGT

    :param device:
    :param firmware: filename of the firmware to be uploaded to the FGT
    :return:
    """
    # url = f"https://{device.ip}:{device.https_port}/api/v2/monitor/system/firmware/upgrade?access_token={device.apikey}"
    url = f"https://{device.ip}:{device.https_port}/api/v2/monitor/system/firmware/upgrade"

    with open(firmware, mode='rb') as f:
        firmware_bytes = f.read()

    firmware_base64 = base64.b64encode(firmware_bytes).decode()  # base64 in string format (without the 'b')

    payload = {'source': 'upload', 'format_partition': False, 'filename': firmware, 'file_content': firmware_base64}

    response = requests.request("POST", url,
                                headers={'accept': 'application/json', 'authorization': 'Bearer '+device.apikey},
                                data=json.dumps(payload),
                                verify=False)

    if response.status_code != 200 or json.loads(response.text).get('status') != 'success':
        print(f'{device.name} : failure during upload of firmware via API: '
              f'status_code={response.status_code} reason={response.reason} \ntext={response.text}')
        print(f'{device.name} : Trying firmware upload via SCP...')
        try:
            configure(device, path='/system/global', payload={'admin-scp': 'enable'}, error_msg='failure to enable SCP')
            fortios.ssh.upload_firmware(device, firmware)
        except Exception as ex:
            # Display detailed information about the exception (class, filename, line number)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            raise StopProcessingDevice(f'{device.name} : failure during upload of firmware via SCP: ',
                                       exc_type, fname, exc_tb.tb_lineno)


def run_script(device: FortiGate, script_name: str):
    """
    Upload and Run CLI configuration script to the FGT

    :param device:
    :param script_name:
    :return:
    """
    # Upload and run script on FGT
    # url = f"https://{device.ip}:{device.https_port}/api/v2/monitor/system/config-script/upload?access_token={device.apikey}"
    url = f"https://{device.ip}:{device.https_port}/api/v2/monitor/system/config-script/upload"

    config_base64_bytes = base64.b64encode(bytes(device.config, "utf-8"))  # base64 in raw (bytes) format (b'...')
    config_base64_string = config_base64_bytes.decode()  # base64 in string format (without the 'b')

    payload = {'filename': script_name, 'file_content': f'{config_base64_string}'}

    response = requests.request("POST", url,
                                headers={'accept': 'application/json', 'authorization': 'Bearer '+device.apikey},
                                data=json.dumps(payload),
                                verify=False)

    if response.status_code != 200:
        # API access failed => skip this device
        raise StopProcessingDevice(f'{device.name} : failure during upload or run of the configuration script'
                                   f'\nstatus_code={response.status_code} reason={response.reason} \ntext={response.text}\n')


def restore_config_file(device: FortiGate):
    """
    Restore full configuration file on FGT

    :param device:
    :return:
    """
    # url = f"https://{device.ip}:{device.https_port}/api/v2/monitor/system/config/restore?access_token={device.apikey}"
    url = f"https://{device.ip}:{device.https_port}/api/v2/monitor/system/config/restore"

    config_base64_bytes = base64.b64encode(bytes(device.config, "utf-8"))  # base64 in raw (bytes) format (b'...')
    config_base64_string = config_base64_bytes.decode()  # base64 in string format (without the 'b')

    payload = {'source': 'upload', 'scope': 'global', 'file_content': config_base64_string}

    response = requests.request("POST", url,
                                headers={'accept': 'application/json', 'authorization': 'Bearer '+device.apikey},
                                data=json.dumps(payload),
                                verify=False)

    if response.status_code != 200:
        # API access failed => skip this device
        raise StopProcessingDevice(f'{device.name} : failure during upload of configuration file'
                                   f'\nstatus_code={response.status_code} reason={response.reason} \ntext={response.text}\n')
