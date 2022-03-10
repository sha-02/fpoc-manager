from django.core.handlers.wsgi import WSGIRequest
from django.template import loader
from config.settings import PATH_FPOC_FIRMWARE, PATH_FPOC_BOOTSTRAP_CONFIGS, RELPATH_FPOC_BOOTSTRAP_CONFIGS, PATH_FPOC_CONFIG_SAVE, BASE_DIR
import threading

import fpoc.fortios as fortios
from fpoc import FortiGate, FortiGate_HA, FortiManager, TypePoC
from fpoc import CompletedDeviceProcessing, StopProcessingDevice, ReProcessDevice, AbortDeployment


def prepare_api(device: FortiGate):
    """
    Create API admin and API key on FGT (via SSH)

    :param device:
    :return:
    """

    # Checks if an API key is associated to the FGT. If no, create API admin/key on the FGT via SSH.
    print(f'{device.name} : Checking if FGT has an API key')

    if not device.apikey:
        # There is no API key for this FGT. Connect to the device via SSH to create an admin api-user (if none exists),
        # generate and retrieve an API key for this admin
        print(f'{device.name} : No API key. Adding an API admin (if none exists) and retrieving his API key via SSH')
        fortios.create_api_admin(device)  # creates API admin (if needed) and updates the device.apikey
        # print(output)

    # There is an API key for this FGT
    print(f'{device.name} : API key is {device.apikey}')


def prepare_fortios_version(device: FortiGate, fos_version_target: str, lock: threading.Lock):
    """
    Retrieves the FOS version running on the FGT and updates device.fos_version accordingly
    :param device:
    :param fos_version_target: FOS version requested by user (e.g. "6.4.6"). 'None' if no FOS version is preferred
    :param lock: mutual exclusion (mutex) lock used to download and store missing firmware
    :return:
    """
    device.fos_version = fortios.retrieve_fos_version(device)  # Update info about the version running on FGT
    print(f"{device.name} : FGT is running FOS {device.fos_version}", end='')
    if fos_version_target and fos_version_target != device.fos_version:
        print(f" but user requested FOS {fos_version_target}: need to update the FOS version")
        print(f"{device.name} : Changing the FGT hostname to 'FIRMWARE_UPDATED' before updating the firmware")
        fortios.change_hostname(device, f'FIRMWARE_UPDATED_{device.name_fpoc}')  # FortiPoC device name is used here
        print(f"{device.name} : Hostname changed")
        update_fortios_version(device, fos_version_target, lock)
        device.apikey = None  # Reset the API key
        raise ReProcessDevice(sleep=90)  # Leave enough time for the FGT to upgrade/downgrade the config and reboot

    print('')  # because of the print("... is running FOS ...", end='')


def update_fortios_version(device: FortiGate, fos_version_target: str, lock: threading.Lock):
    """
    Update (upgrade or downgrade) the FOS version running on this FGT
    :param device:
    :param fos_version_target: FOS version requested by user (e.g. "6.4.6")
    :param lock: mutual exclusion (mutex) lock used to download and store missing firmware
    :return:
    """

    # List of supported fortios firmware
    firmwares = fortios_firmware()

    # Check if the target firmware is referenced
    if firmwares.get(fos_version_target) is None:
        print(f'{device.name} : Firmware {fos_version_target} is not referenced')
        raise StopProcessingDevice

    # Check if the target firmware file is available
    lock.acquire()  # Acquire the mutual exclusion (mutex) lock to ensure only one thread at a time goes through this code

    # firmware filename can also be prefixed by the version. So filename can be, for e.g.:
    # - 'FGT_VM64_KVM-v6-build1911-FORTINET.out'
    # - or '6.4.7_FGT_VM64_KVM-v6-build1911-FORTINET.out'
    for firmware in (firmwares[fos_version_target]["filename"],
                     fos_version_target + '_' + firmwares[fos_version_target]["filename"]):
        try:
            with open(f'{PATH_FPOC_FIRMWARE}/{firmware}', "rb"):
                break
        except FileNotFoundError:
            pass
    else:
        print(f'{device.name} : Firmware not found in folder {PATH_FPOC_FIRMWARE}')
        print(f'{device.name} : Downloading firmware image from store... ')
        firmware = firmwares[fos_version_target]["filename"]
        firmware_download(firmware)
        print(f'{device.name} : Download completed.')

    # release the lock so that other treads can now check the existence of the firmware file
    lock.release()

    print(f'{device.name} : Found firmware {firmware} in folder {PATH_FPOC_FIRMWARE}')
    print(f'{device.name} : Uploading firmware... ')
    fortios.upload_firmware(device, firmware)
    print(f'{device.name} : Firmware uploaded.')


def fortios_firmware() -> dict:
    """
    Load the fortios firmware dictionary from JSON file
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

    with open(f'{PATH_FPOC_FIRMWARE}/{firmware}', "wb") as f:
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


def is_running_ha(device: FortiGate) -> bool:
    """
    Retrieve the HA status of the FGT via API (FOS >= 6.2.2) or via SSH otherwise
    Returns True if running HA, False otherwise
    :param device:
    :return:
    """
    if device.FOS >= 6_002_002:
        ha = fortios.api.is_running_ha(device)
    else:
        ha = fortios.ssh.is_running_ha(device)

    if ha:
        print(f'{device.name} : FGT is running HA')
        return True

    print(f'{device.name} : FGT is not running HA')
    return False


def is_running_bootstrap(device: FortiGate) -> bool:
    """
    Check if FGT is running a bootstrap config (its hostname contains 'BOOTSTRAP_CONFIG'). Return True or False.
    """
    bootstrap = 'BOOTSTRAP_CONFIG' in retrieve_hostname(device)
    if bootstrap:
        print(f'{device.name} : FGT is running a bootstrap config (its hostname contains "BOOTSTRAP_CONFIG")')
    else:
        print(f'\n{device.name} : FGT is not running a boostrap configuration')

    return bootstrap


def render_bootstrap_config(device: FortiGate):
    """
    Render the bootstrap config based on the FortiOS version of the FGT (device.fos_version)
    Bootstrap config is stored in device.config

    :param device:
    :return:
    """

    # Check if there is a bootstrap config for this FOS firmware on the disk (file name e.g. '6.4.6.out')
    try:
        with open(f'{PATH_FPOC_BOOTSTRAP_CONFIGS}/{device.fos_version}.conf', mode='r') as f:
            f.read()
    except:
        print(
            f'{device.name} : Could not find bootstrap configuration "{device.fos_version}.conf" in folder {PATH_FPOC_BOOTSTRAP_CONFIGS}')
        raise StopProcessingDevice

    # Render the bootstrap configuration

    device.template_context['ip'] = device.mgmt_ipmask  # mgmt IP in the OOB MGMT subnet (e.g., 172.16.31.12/24)
    device.template_context['FOS'] = device.FOS  # FOS version as long integer, like 6_000_013 for '6.0.13'
    device.template_context['mgmt_subnet'] = device.mgmt_subnet  # e.g. 172.16.31.0/24
    device.template_context['mgmt_fpoc'] = device.mgmt_fpoc_ip  # e.g., 172.16.31.254
    device.template_context['mgmt_interface'] = device.mgmt_interface
    device.template_context['apiadmin'] = device.apiadmin
    device.template_context['HA'] = device.ha

    # No need to pass the 'request' (which adds CSRF tokens) since this is a rendering for FGT CLI settings
    device.config = loader.render_to_string(f'{RELPATH_FPOC_BOOTSTRAP_CONFIGS}/{device.fos_version}.conf',
                                            device.template_context, using='jinja2')


def upload_bootstrap_config(device: FortiGate):
    """
    Upload the bootstrap configuration stored in device.config
    """
    print(f'{device.name} : Uploading bootstrap configuration... ')
    fortios.restore_config_file(device)
    print(f'{device.name} : bootstrap configuration uploaded.')


def should_upload_boostrap(device: FortiGate) -> bool:
    """
    Check if bootstrap config must be uploaded to FGT or not
    Returns Boolean: True if should upload bootstrap, False otherwise
    """
    running_ha = is_running_ha(device)

    if running_ha and device.ha.mode == FortiGate_HA.Modes.STANDALONE:
        print(f"{device.name} : HA is running on FGT but 'standalone' mode must be deployed")
        return True

    if not running_ha and device.ha.mode != FortiGate_HA.Modes.STANDALONE:
        print(f"{device.name} : HA must be deployed but FGT is running in 'standalone' mode")
        return True

    if device.ha.mode != FortiGate_HA.Modes.STANDALONE:
        print(f"{device.name} : HA must be deployed")

    if not is_running_bootstrap(device):  # FGT is not running bootstrap config
        return True

    return False


def save_config(fortipoc_name: str, device: FortiGate, poc_id: int):
    """
    """
    filename = f'{PATH_FPOC_CONFIG_SAVE}/{fortipoc_name}_poc{poc_id:02}_{device.name}.conf'
    with open(filename, 'w') as f:
        if is_config_snippets(device.config):
            f.write(f'# fpoc{poc_id:02} {device.name} FortiOS {device.fos_version}')
            f.write(f'\n# context = {device.template_context}')
            f.write('\n#\n' + '#' * 50)
        f.write(device.config)

    if poc_id == 0:
        print(f'{device.name} : Bootstrap configuration saved to {filename}')
    elif is_config_snippets(device.config):
        print(f'{device.name} : CLI script saved to {filename}')
    else:
        print(f'{device.name} : full-config saved to {filename}')


def deploy(request: WSGIRequest, poc: TypePoC, device: FortiGate):
    """
    Render the configuration (Django template) and deploy it to the FGT

    :param request:
    :param poc:
    :param device:
    :return:
    """

    # Prepare the FGT: API admin, API key and FortiOS version
    #
    if request.POST.get('previewOnly') and request.POST.get('targetedFOSversion'):
        device.fos_version = request.POST['targetedFOSversion']  # FOS version assigned to FGTs for config rendering
    else:
        prepare_api(device)  # create API admin and key if needed
        # ensure FGT runs the desired FortiOS version if user asked for a specific FOS version
        prepare_fortios_version(device, fos_version_target=request.POST.get('targetedFOSversion'), lock=poc.lock)

    # Special PoC which only uploads bootstrap config to the FGT
    #
    if poc.id == 0:
        device.template_context['fmg_ip'] = poc.devices['FMG'].mgmt_ip if any(
            (True for dev in poc.devices.values() if isinstance(dev, FortiManager))) else None  # mgmt IP of FMG (if any), otherwise None
        render_bootstrap_config(device)
        if not request.POST.get('previewOnly') and should_upload_boostrap(device):
            upload_bootstrap_config(device)
            save_config(poc.__class__.__name__, device, 0)  # Save the bootstrap config
        raise CompletedDeviceProcessing

    # Render the config (CLI script or full-config)
    # Upload bootstrap config (if CLI script)
    # Deploy the config (CLI script of full-config)
    #

    # Add information to the template context of this device
    device.template_context['fos_version'] = device.fos_version  # FOS version encoded as a string like '6.0.13'
    device.template_context['FOS'] = device.FOS  # FOS version as long integer, like 6_000_013 for '6.0.13'
    device.template_context['mgmt_fpoc'] = device.mgmt_fpoc_ip  # 172.16.31.254
    device.template_context['HA'] = device.ha
    device.template_context['wan'] = device.wan
    device.template_context['fmg_ip'] = poc.devices['FMG'].mgmt_ip if any(
        (True for dev in poc.devices.values() if isinstance(dev, FortiManager))) else None  # mgmt IP of FMG (if any), otherwise None
    device.template_context['FMG_FORTIGATE_ID'] = None

    # No need to pass the 'request' (which adds CSRF tokens) since this is a rendering for FGT CLI settings
    device.config = loader.render_to_string(f'fpoc/{poc.__class__.__name__}/poc{poc.id:02}/{device.template_group}/{device.template_filename}',
                                            device.template_context, using='jinja2')
    # print(cli_settings)

    # if the config is not a full-config: Upload bootstrap config to FGT (if it is not running one)
    if not request.POST.get('previewOnly') and is_config_snippets(device.config) and should_upload_boostrap(device):
        render_bootstrap_config(device)
        upload_bootstrap_config(device)
        save_config(poc.__class__.__name__, device, 0)  # Save the bootstrap config
        if device.ha.mode == FortiGate_HA.Modes.FGCP and device.ha.role == FortiGate_HA.Roles.SECONDARY:
            raise CompletedDeviceProcessing
        else:
            device.apikey = None  # reset cached API key since there is no API key in the bootstrap config
            raise ReProcessDevice(sleep=90)  # Leave enough time for the FGT to load the config and reboot

    # Save this CLI configuration to disk
    save_config(poc.__class__.__name__, device, poc.id)

    # Deploy the config
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
    # revision_name = f' fpoc={poc.id:02} context={device.template_context}'
    # print(f'Saving the configuration in the revision history: {revision_name}')
    # fortios.save_to_revision(device, revision_name)


def is_config_snippets(config: str) -> bool:
    """
    """
    return not ('config-version=' in config)  # 'True' if config snippet, 'False' if full FOS config file


# Legacy functions from previous version ############################################################################


def __old__prepare_bootstrap(device: FortiGate):
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
