from django.core.handlers.wsgi import WSGIRequest
from django.template import loader
from config.settings import BASE_DIR

import fpoc.fortios as fortios
from fpoc.devices import FortiGate
from fpoc.exceptions import CompletedDeviceProcessing, StopProcessingDevice, ReProcessDevice, AbortDeployment
from fpoc.fortipoc import TypePoC


def prepare_api(device: FortiGate):
    """
    Create API admin and API key on FGT (via SSH)

    :param device:
    :return:
    """

    # Checks if an API key is associated to the FGT. If no, create API admin/key on the FGT via SSH.
    print(f'{device.name} : Checking if FGT has an API key')

    if not device.apikey:
        # There is no API key for this FGT. Connect to the device via SSH to create an admin api-user,
        # generate and retrieve an API key for this admin
        print(f'{device.name} : No API key. Adding an API admin and retrieving an API key via an SSH session')

        fortios.create_api_admin(device)  # creates API admin and updates the device.apikey
        # print(output)

    # There is an API key for this FGT
    print(f'{device.name} : API key is {device.apikey}')


def prepare_fortios_version(device: FortiGate, fos_version_target: str):
    """
    Retrieves the FOS version running on the FGT and updates device.fos_version accordingly
    :param fos_version_target: FOS version requested by user (e.g. "6.4.6"). 'None' if no FOS version is preferred
    :param device:
    :return:
    """
    device.fos_version = fortios.retrieve_fos_version(device)  # Update info about the version running on FGT
    print(f"{device.name} : FGT is running FOS {device.fos_version}", end='')
    if fos_version_target and fos_version_target != device.fos_version:
        print(f" but user requested FOS {fos_version_target}: need to update the FOS version")
        print(f"{device.name} : Changing the FGT hostname to 'FIRMWARE_UPDATED' before updating the firmware")
        fortios.change_hostname(device, 'FIRMWARE_UPDATED')
        print(f"{device.name} : Hostname changed")
        update_fortios_version(device, fos_version_target)

    print('')  # because of the print("... is running FOS ...", end='')


def update_fortios_version(device: FortiGate, fos_version_target: str):
    """
    Update (upgrade or downgrade) the FOS version running on this FGT
    :param fos_version_target: FOS version requested by user (e.g. "6.4.6")
    :param device:
    :return:
    """

    # List of supported fortios firmware
    firmwares = fortios_firmware()

    # Check if the target firmware is referenced
    if firmwares.get(fos_version_target) is None:
        print(f'{device.name} : Firmware {fos_version_target} is not referenced')
        raise StopProcessingDevice

    # Check if the target firmware file is available
    # firmware filename can also be prefixed by the version. So filename can be, for e.g.:
    # - 'FGT_VM64_KVM-v6-build1911-FORTINET.out'
    # - or '6.4.7_FGT_VM64_KVM-v6-build1911-FORTINET.out'
    firmware_path = f'{BASE_DIR}/templates/firmware'
    for firmware in (firmwares[fos_version_target]["filename"], fos_version_target+'_'+firmwares[fos_version_target]["filename"]):
        try:
            with open(f'{firmware_path}/{firmware}', "rb") as f:
                break
        except FileNotFoundError:
            pass
    else:
        print(f'{device.name} : Firmware not found in folder {firmware_path}')
        print(f'{device.name} : Downloading firmware image from store... ', end='')
        firmware = firmwares[fos_version_target]["filename"]
        firmware_download(firmware)
        print("Download completed.")

    print(f'{device.name} : Found firmware {firmware} in folder {firmware_path}')
    print(f'{device.name} : Uploading firmware... ', end='')
    fortios.upload_firmware(device, firmware)
    print('Firmware uploaded.')
    raise ReProcessDevice(sleep=90)  # Leave enough time for the FGT to upgrade/dowgrade the config and reboot


def fortios_firmware() -> dict:
    """
    Load the fortios firmware dictionnary from JSON file
    :return: dict of fos firmware
    """
    import json

    try:
        with open(f'{BASE_DIR}/fpoc/fortios/firmware.json', "r") as f:
            return json.loads(f.read())
    except FileNotFoundError:
        print(f'File not found: {BASE_DIR}/fpoc/fortios/firmware.json')
        raise AbortDeployment


def firmware_download(firmware: str):
    """

    :param firmware: contains the filename of the firmware to download from store
    :return:
    """
    import requests

    download_url = f"https://labsetup1.repository.fortipoc.etlab.net/store/images/{firmware}"

    response = requests.get(download_url, verify=False)
    response.raise_for_status()  # Check that the request was successful

    firmware_path = f'{BASE_DIR}/templates/firmware'
    with open(f'{firmware_path}/{firmware}', "wb") as f:
        f.write(response.content)


def retrieve_hostname(device: FortiGate) -> str:
    """
    Retrieve the hostname of the FGT via API (FOS >= 6.4.3) or via SSH otherwise
    :param device:
    :return:
    """
    if device.FOS >= 6_004_003:
        return fortios.api.retrieve_hostname(device)

    return fortios.ssh.retrieve_hostname(device)


def prepare_bootstrap_config(device: FortiGate):
    """
    Check if FGT is running a bootstrap config (hostname is 'BOOSTRAP_CONFIG')
    If FGT is not running bootstrap config upload a bootstrap config to the FGT for its firmware version

    :param device:
    :return:
    """
    import ipaddress

    # Check if FGT is running a bootstrap config (hostname is 'BOOTSTRAP_CONFIG')
    print(f'{device.name} : Checking if FGT is running a bootstrap config (hostname is "BOOTSTRAP_CONFIG")', end='')
    if retrieve_hostname(device) == 'BOOTSTRAP_CONFIG':
        print(f' => Yes')
        return None

    print(f'\n{device.name} : FGT is not running a boostrap configuration, need to upload bootstrap config for {device.fos_version}')

    # Check if there is a bootstrap config for this FOS firmware on the disk (file name e.g. '6.4.6.out')
    bootstrap_path = f'{BASE_DIR}/templates/fpoc/fpoc00/bootstrap_configs'
    try:
        with open(f'{bootstrap_path}/{device.fos_version}.conf', mode='r') as f:
            config = f.read()
    except:
        print(f'{device.name} : Could not find bootstrap configuration "{device.fos_version}.conf" in folder {bootstrap_path}')
        raise (StopProcessingDevice)

    # Render the bootstrap configuration

    context = {
        'ip': device.mgmt_ip,  # mgmt IP of the device in the OOB MGMT subnet (e.g., 172.16.31.12)
        'mgmt_fpoc': ipaddress.ip_interface(device.mgmt_fpoc).ip.compressed  # management IP of the FortiPoC inside the
        # OOB mgmt subnet (e.g., 172.16.31.254)
    }

    device.config = loader.render_to_string(f'fpoc/fpoc00/bootstrap_configs/{device.fos_version}.conf',
                                            context, request=None)

    # Upload the bootstrap configuration to the FGT
    print(f'{device.name} : Uploading bootstrap configuration... ', end='')
    fortios.restore_config_file(device)
    print('bootstrap configuration uploaded.')
    device.apikey = None  # reset cached API key since there is no API key in the bootstrap config
    raise ReProcessDevice(sleep=60)  # Leave enough time for the FGT to load the config and reboot


def deploy_config(request: WSGIRequest, poc: TypePoC, device: FortiGate):
    """
    Render the configuration (Django template) and deploy it to the FGT

    :param request:
    :param device:
    :return:
    """
    import ipaddress

    # Prepare the FGT
    #
    if request.POST.get('previewOnly') and request.POST.get('targetedFOSversion'):
            device.fos_version = request.POST['targetedFOSversion'] # FOS version assigned to FGTs for config rendering
    else:
        # Retrieve the FOS version running on the FGT and ensure FGT is ready for deployment:
        #   - it runs the desired FortiOS version if user asked for a specific FOS version
        #   - it has an API admin, an API key,
        #   - it is running bootstrap configuration
        prepare_api(device)  # create API admin and key
        prepare_fortios_version(device, fos_version_target=request.POST.get('targetedFOSversion'))

    # Render the config
    #

    # Add information to the template context of this device: its FortiOS version and its WAN settings
    device.template_context['fos_version'] = device.fos_version  # FOS version encoded as a string like '6.0.13'
    device.template_context['FOS'] = device.FOS  # FOS version as long integer, like 6_000_013 for '6.0.13'
    device.template_context['mgmt_fpoc'] = ipaddress.ip_interface(device.mgmt_fpoc).ip.compressed  # 172.16.31.254
    device.template_context['wan'] = device.wan

    device.config = loader.render_to_string(f'fpoc/fpoc{poc.id:02}/{device.template_group}/{device.template_filename}',
                                            device.template_context, request)
    # print(cli_settings)

    if not request.POST.get('previewOnly') and is_config_snippets(device.config):
        prepare_bootstrap_config(device)  # Ensure FGT is running a bootstrap config before applying CLI settings script

    # Save this CLI configuration script to disk
    filename = f'{BASE_DIR}/templates/fpoc/configs/fpoc{poc.id:02}_{device.name}.conf'
    with open(filename, 'w') as f:
        if is_config_snippets(device.config):
            f.write(f'# fpoc{poc.id:02} {device.name} FortiOS {device.fos_version}')
            f.write(f'\n# context = {device.template_context}')
            f.write('\n#\n' + '#' * 50)
        f.write(device.config)

    print(f'{device.name} : Configuration saved to {filename}')

    # Deploy the config
    #
    if request.POST.get('previewOnly'):  # Only preview of the config is requested, no deployment needed
        raise CompletedDeviceProcessing  # No more processing needed for this FGT

    if is_config_snippets(device.config):
        # Execute the CLI settings in device.config on the FGT and Save them in the 'Script' repository of the FGT
        script_name = f'fpoc={poc.id:02} config_hash={hash(device.config):_}'
        print(f'{device.name} : Upload and run configuration script: {script_name}')
        fortios.run_script(device, script_name)
    else:
        # Full configuration file
        print(f'{device.name} : Restoring full configuration')
        fortios.restore_config_file(device)

    # Save this configuration in the config revision
    # revision_name = f'fpoc={poc.id:02} context={device.template_context}'
    # print(f'Saving the configuration in the revision history: {revision_name}')
    # fortios.save_to_revision(device, revision_name)


def is_config_snippets(config: str) -> bool:
    return not ('config-version=' in config)  # 'True' if config snippet, 'False' if full FOS config file


# Legacy functions from previous version ############################################################################


def _OLD__prepare_bootstrap(device: FortiGate):
    """
    Check if FGT is running a bootstrap config. Save it to revision if not already done.
        If FGT is not running bootstrap config, revert to bootstrap revision if there is one
        If FGT is not running bootstrap config and there is no bootstrap revision, stop processing this device

    :param device:
    :return:
    """

    # Check if FGT has a bootstrap config in the revision
    print('Checking if there is a bootstrap config in the revision', end='')
    fgt_bootstrap_revision_id = fortios.check_having_bootstrap_revision(device)
    print(f' => {fgt_bootstrap_revision_id}')

    # Check if FGT is running a bootstrap config
    print('Checking if FGT is running a bootstrap config', end='')
    fgt_is_running_bootstrap = fortios.check_running_bootstrap(device)
    print(f' => {fgt_is_running_bootstrap}')

    # Not running bootstrap & no bootstrap in revision => skip device
    if not fgt_is_running_bootstrap and not fgt_bootstrap_revision_id:
        raise StopProcessingDevice(f'{device.name} : FGT is not running a bootstrap config'
                                   f' and there is no boostrap config in the revision history')

    # Running bootstrap & no bootstrap in revision => save running bootstrap config in revision
    if fgt_is_running_bootstrap and not fgt_bootstrap_revision_id:
        print('FGT is running a bootstrap config but has no bootstrap revision yet. '
              'Saving the bootstrap config in the revision.')
        fortios.save_to_revision(device, comment='bootstrap configuration')

    # Not running bootstrap & bootstrap in revision => revert to bootstrap config revision
    if not fgt_is_running_bootstrap and fgt_bootstrap_revision_id:
        print('FGT is not running a bootstrap config. However, there is a bootstrap config in the revision. '
              'Reverting to the bootstrap configuration.')
        fortios.revert_to_revision(device, fgt_bootstrap_revision_id)  # Reload the bootstrap config on the FGT
        device.apikey = None  # FGT will reboot with no API key
        raise ReProcessDevice(sleep=30)  # Raise exception to re-process FGT, asking the exception handler to sleep 30s

    # Running bootstrap & bootstrap revision
    print('FGT is running a boostrap config and has a bootstrap revision')
