import base64
import re

import json
import requests
import urllib3
from requests.exceptions import Timeout

from config.settings import PATH_FPOC_FIRMWARE
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
def retrieve_access_token(device: FortiGate) -> str:
    """
    Retrieve an access_token using APIv2 admin/password authentication without the need to create an API admin (api-user) via SSH

    :param device:
    :return:
    """

    url = f"https://{device.ip}:{device.https_port}/api/v2/authentication"

    payload = {'username': device.username, 'secretkey': device.password, 'ack_post_disclaimer': True, 'request_key': True }
    response = requests.request("POST", url, headers={'accept': 'application/json'}, data=json.dumps(payload),
                                verify=False)

    if response.status_code != 200:
        # API access failed => skip this device
        raise RetryProcessingDevice(f'{device.name} : failure to retrieve an access_token using APIv2 admin/password authentication'
                                   f'\nstatus_code={response.status_code} reason={response.reason} \ntext={response.text}\n')

    response_json = response.json()
    # pprint(response_json)

    # return the access_token
    return response_json['session_key']


def retrieve_hostname(device: FortiGate) -> str:
    """
    Retrieve the hostname of the FGT

    :param device:
    :return:
    """

    url = f"https://{device.ip}:{device.https_port}" \
          f"/api/v2/monitor/system/status?access_token={device.apikey}"

    # print(url)
    response = requests.request("GET", url, headers={'accept': 'application/json'}, verify=False)
    if response.status_code != 200:
        # API access failed => skip this device
        raise RetryProcessingDevice(f'{device.name} : failure to retrieve FGT hostname'
                                   f'\nstatus_code={response.status_code} reason={response.reason} \ntext={response.text}\n')

    response_json = response.json()
    # pprint(response_json)

    return response_json['results']['hostname']


def is_running_ha(device: FortiGate) -> bool:
    """
    Retrieve the HA peers of the FGT

    :param device:
    :return:
    """

    url = f"https://{device.ip}:{device.https_port}" \
          f"/api/v2/monitor/system/ha-peer?access_token={device.apikey}"

    # print(url)
    response = requests.request("GET", url, headers={'accept': 'application/json'}, verify=False)
    if response.status_code != 200:
        # API access failed => skip this device
        raise RetryProcessingDevice(f'{device.name} : failure to retrieve HA status of FGT'
                                   f'\nstatus_code={response.status_code} reason={response.reason} \ntext={response.text}\n')

    response_json = response.json()
    # pprint(response_json)

    # 'results' is a list of all HA peers. List is empty if no HA.
    return bool(len(response_json['results']))


def change_hostname(device: FortiGate, hostname: str):
    """
    Change the Hostname on the FGT

    :param device:
    :param hostname:
    :return:
    """
    url = f"https://{device.ip}:{device.https_port}/api/v2/cmdb/system/global?access_token={device.apikey}"
    # print(url)

    payload = {'hostname': hostname}
    response = requests.request("PUT", url, headers={'accept': 'application/json'}, data=json.dumps(payload),
                                verify=False)

    if response.status_code != 200:
        # API access failed => skip this device
        raise RetryProcessingDevice(f'{device.name} : failure during update of firmware'
                                   f'\nstatus_code={response.status_code} reason={response.reason} \ntext={response.text}\n')


def retrieve_fos_version(device: FortiGate) -> str:
    """
    Get the FOS version running on the FGT and update device.fos_version accordingly

    :param device:
    :return:
    """

    url = f"https://{device.ip}:{device.https_port}" \
          f"/api/v2/monitor/system/status?access_token={device.apikey}"

    # print(url)
    response = requests.request("GET", url, headers={'accept': 'application/json'}, verify=False)
    if response.status_code != 200:
        # API access failed => skip this device
        raise RetryProcessingDevice(f'{device.name} : failure to retrieve FortiOS version'
                                   f'\nstatus_code={response.status_code} reason={response.reason} \ntext={response.text}\n')

    response_json = response.json()
    # pprint(response_json)

    # Updates the FOS version => string returned by JSON is e.g. "v6.4.4", so need to only keep "6.4.4"
    return response_json['version'][1:]


def upload_firmware(device: FortiGate, firmware: str):
    """
    Update (upgrade or downgrade) the firmware of this FGT

    :param device:
    :param firmware: filename of the firmware to be uploaded to the FGT
    :return:
    """
    url = f"https://{device.ip}:{device.https_port}" \
          f"/api/v2/monitor/system/firmware/upgrade?access_token={device.apikey}"

    # print(url)
    with open(f'{PATH_FPOC_FIRMWARE}/{firmware}', mode='rb') as f:
        firmware_bytes = f.read()

    firmware_base64 = base64.b64encode(firmware_bytes).decode()  # base64 in string format (without the 'b')

    payload = {'source': 'upload', 'format_partition': False, 'filename': firmware, 'file_content': firmware_base64}

    response = requests.request("POST", url, headers={'accept': 'application/json'}, data=json.dumps(payload),
                                verify=False)

    if response.status_code != 200:
        # API access failed => skip this device
        raise StopProcessingDevice(f'{device.name} : failure during update of firmware'
                                   f'\nstatus_code={response.status_code} reason={response.reason} \ntext={response.text}\n')


def run_script(device: FortiGate, script_name: str):
    """
    Upload and Run CLI configuration script to the FGT

    :param device:
    :param script_name:
    :return:
    """
    # Upload and run script on FGT
    url = f"https://{device.ip}:{device.https_port}" \
          f"/api/v2/monitor/system/config-script/upload?access_token={device.apikey}"

    # print(url)
    config_base64_bytes = base64.b64encode(bytes(device.config, "utf-8"))  # base64 in raw (bytes) format (b'...')
    config_base64_string = config_base64_bytes.decode()  # base64 in string format (without the 'b')

    payload = {'filename': script_name, 'file_content': f'{config_base64_string}'}

    response = requests.request("POST", url, headers={'accept': 'application/json'}, data=json.dumps(payload),
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
    url = f"https://{device.ip}:{device.https_port}" \
          f"/api/v2/monitor/system/config/restore?access_token={device.apikey}"

    config_base64_bytes = base64.b64encode(bytes(device.config, "utf-8"))  # base64 in raw (bytes) format (b'...')
    config_base64_string = config_base64_bytes.decode()  # base64 in string format (without the 'b')

    payload = {'source': 'upload', 'scope': 'global', 'file_content': config_base64_string}

    response = requests.request("POST", url, headers={'accept': 'application/json'}, data=json.dumps(payload),
                                verify=False)

    if response.status_code != 200:
        # API access failed => skip this device
        raise StopProcessingDevice(f'{device.name} : failure during upload of configuration file'
                                   f'\nstatus_code={response.status_code} reason={response.reason} \ntext={response.text}\n')


# Legacy functions from previous version ############################################################################
#
# def check_running_bootstrap(device: FortiGate):
#     """
#     Check if the FGT is currently running a bootstrap configuration
#
#     :param device:
#     :return: True if the is running bootstrap config, False otherwise
#     """
#
#     url = f"https://{device.ip}:{device.https_port}" \
#           f"/api/v2/cmdb/system/global?access_token={device.apikey}"
#
#     # print(url)
#     response = requests.request("GET", url, headers={'accept': 'application/json'}, verify=False)
#     if response.status_code != 200:
#         # API access failed => skip this device
#         raise StopProcessingDevice(f'{device.name} : failure to retrieve the hostname'
#                                    f'\nstatus_code={response.status_code} reason={response.reason} \ntext={response.text}\n')
#
#     response_json = response.json()
#     # pprint(response_json)
#
#     # Returns True if hostname is of the form "FGVM<12-alphanumeric>" (i.e., FGT is running a bootstrap config).
#     # Returns False otherwise
#     return bool(re.match('FGVM\w{12,12}', response_json['results']['hostname']))
#
#
# def check_having_bootstrap_revision(device: FortiGate):
#     """
#     Check if there is a bootstrap config in the FGT revision history.
#
#     :param device:
#     :return: True if there is a bootstrap revision. False otherwise.
#     """
#
#     url = f"https://{device.ip}:{device.https_port}" \
#           f"/api/v2/monitor/system/config-revision?access_token={device.apikey}"
#
#     # print(url)
#     response = requests.request("GET", url, headers={'accept': 'application/json'}, verify=False)
#     if response.status_code != 200:
#         # API access failed => skip this device
#         raise StopProcessingDevice(f'{device.name} : failure to retrieve the revision history'
#                                    f'\nstatus_code={response.status_code} reason={response.reason} \ntext={response.text}\n')
#
#     response_json = response.json()
#     # pprint(response_json)
#
#     # List of all revision-id which have a comment of 'bootstrap revision'
#     bootstrap_revision_id_list = [revision['id'] for revision in response_json['results']['revisions'] if
#                                   revision['comment'] == 'bootstrap configuration']
#
#     # Returns the revision-id if there is a bootstrap configuration in the revision history. Returns None otherwise.
#     if bootstrap_revision_id_list:
#         return bootstrap_revision_id_list.pop()  # any of the revision-id is ok, so just pop the last in the list
#
#
# def save_to_revision(device: FortiGate, comment: str):
#     """
#     Save the current configuration running on the FGT into the revision history
#
#     :param device:
#     :param comment:
#     :return:
#     """
#     # Save the running config (bootstrap) in the revision history
#     url = f"https://{device.ip}:{device.https_port}" \
#           f"/api/v2/monitor/system/config-revision/save?access_token={device.apikey}" \
#           f"&comments={comment}"
#
#     # print(url)
#     response = requests.request("POST", url, headers={'accept': 'application/json'}, verify=False)
#     if response.status_code != 200:
#         # API access failed => skip this device
#         raise StopProcessingDevice(f'{device.name} : failure to save the revision'
#                                    f'\nstatus_code={response.status_code} reason={response.reason} \ntext={response.text}\n')
#
#
# def revert_to_revision(device: FortiGate, revision_id: int):
#     """
#     Revert the configuration to a specific revision ID
#
#     :param device:
#     :param revision_id:
#     :return:
#     """
#     url = f"https://{device.ip}:{device.https_port}" \
#           f"/api/v2/monitor/system/config/restore?access_token={device.apikey}"
#
#     # print(url)
#     payload = {'source': 'revision', 'scope': 'global', 'config_id': revision_id}
#
#     try:
#         response = requests.request("POST", url, headers={'accept': 'application/json'}, data=json.dumps(payload),
#                                     timeout=(5, 30), verify=False)
#     except Timeout:
#         device.apikey = None  # Clear the API key since FGT is supposed to restart with bootstrap
#         raise  # propagate the exception up the chain
#
#     if response.status_code != 200:
#         # API access failed => skip this device
#         raise StopProcessingDevice(f'{device.name} : failure when reverting to the bootstrap revision'
#                                    f'\nstatus_code={response.status_code} reason={response.reason} \ntext={response.text}\n')
