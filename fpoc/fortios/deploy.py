from django.template import loader
from config.settings import PATH_FPOC_FIRMWARE, PATH_FPOC_BOOTSTRAP_CONFIGS, RELPATH_FPOC_BOOTSTRAP_CONFIGS, PATH_FPOC_CONFIG_SAVE, BASE_DIR
import threading

import fpoc.fortios as fortios
from fpoc import FortiGate, FortiGate_HA, TypePoC, json_to_dict
from fpoc import CompletedDeviceProcessing, StopProcessingDevice, ReProcessDevice


def prepare_api(device: FortiGate):
    """
    If no API key (access_token) is yet associated to the FGT then retrieve one via the APIv2 ad,in/password authentication
    Nothing to do if the FGT is already associated to an API key (access_token)

    :param device:
    :return:
    """

    # Checks if an API key is associated to the FGT. If no, create API admin/key on the FGT via SSH.
    # print(f'{device.name} : Checking if FGT has an API key')

    if not device.apikey and device.apiv2auth:
        # There is no API key (access_token) for this FGT. Get it via APIv2 using admin/password
        print(f'{device.name} : No API key. Retrieving an access_token using APIv2 admin/password authentication')
        device.apikey = fortios.api.retrieve_access_token(device)

    if not device.apikey and not device.apiv2auth:
        # There is no API key for this FGT. Connect to the device via SSH to create an admin api-user (if none exists),
        # generate and retrieve an API key for this admin
        print(f'{device.name} : No API key. Adding an API admin (if none exists) and retrieving his API key via SSH')
        fortios.create_api_admin(device)  # creates API admin (if needed) and updates the device.apikey

    # print(output)

    # There is an API key for this FGT
    print(f'{device.name} : API key is {device.apikey}')


def prepare_fortios_version(device: FortiGate, fos_version_target: str, FOS_minimum: int, lock: threading.Lock):
    """
    Retrieves the FOS version running on the FGT and updates device.fos_version accordingly
    :param device:
    :param fos_version_target: FOS version requested by user (e.g. "6.4.6"). Empty string ('')' if no FOS version is preferred
    :param FOS_minimum: minimum FOS version which must be running on the FGT (imposed by the feature set). integer (e.g., 7_002_000)
    :param lock: mutual exclusion (mutex) lock used to download and store missing firmware
    :return:
    """
    device.fos_version = fortios.retrieve_fos_version(device)  # Update info about the version running on FGT (string, for e.g. '7.2.5')
    print(f"{device.name} : FGT is running FOS {device.fos_version}", end='')

    # if the target version is not specified and the minimum version is not honored on the device then skip the device
    if not fos_version_target and FOS_minimum > device.FOS:
        raise StopProcessingDevice(f'the minimum FOS version required by the feature set is {FOS_minimum:_}')

    # if the target version is specified, it is already compatible with the minimum version (check was done previously)
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
    firmware_names = (device.model + firmwares[fos_version_target]["trailername"],
                       fos_version_target + '_' + device.model + firmwares[fos_version_target]["trailername"])
    for firmware_name in firmware_names:
        try:
            with open(f'{PATH_FPOC_FIRMWARE}/{firmware_name}', "rb"):   # Check if firmware file exists
                break
        except FileNotFoundError:
            pass
    else:
        print(f'{device.name} : Firmware {fos_version_target} for model {device.model} not found in folder {PATH_FPOC_FIRMWARE}')
        lock.release()
        raise StopProcessingDevice
        # print(f'{device.name} : Downloading firmware image from store... ')
        # firmware = firmwares[fos_version_target]["filename"]
        # firmware_download(firmware)
        # print(f'{device.name} : Download completed.')

    # release the lock so that other treads can now check the existence of the firmware file
    lock.release()

    print(f'{device.name} : Found firmware {fos_version_target} for model {device.model} in folder {PATH_FPOC_FIRMWARE}')
    print(f'{device.name} : Uploading firmware... ')
    fortios.upload_firmware(device, firmware_name)
    print(f'{device.name} : Firmware uploaded.')


def fortios_firmware(minimum: str ="0.0.0") -> dict:
    """
    Load the fortios firmware dictionary from JSON file
    minumum: minimum FOS version desired (default= all versions) - dotted FOS version, eg. '7.4.4'
    :return: dict of fos firmware
    """
    firmware = json_to_dict(f'{BASE_DIR}/fpoc/fortios/firmware.json')   # Load all firmware definition
    # Return firmware with higher version then 'minimum'
    return { version: firmware[version] for version in firmware.keys() if FortiGate.FOS_int(version) >= FortiGate.FOS_int(minimum) }

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


def render_bootstrap_config(poc: TypePoC, device: FortiGate):
    """
    Render the bootstrap config based on the FortiOS version of the FGT (device.fos_version)
    Bootstrap config is stored in device.config

    :param device:
    :return:
    """

    # Check if there is a bootstrap config for this FOS firmware on the disk (file name e.g. '6.4.6.out')
    bootstrap_filename = f'{device.model}_{device.fos_version}.conf'
    try:
        with open(f'{PATH_FPOC_BOOTSTRAP_CONFIGS}/{bootstrap_filename}', mode='r') as f:
            f.read()
    except:
        print(
            f'{device.name} : Could not find bootstrap configuration "{bootstrap_filename}" in folder {PATH_FPOC_BOOTSTRAP_CONFIGS}')
        raise StopProcessingDevice

    # Render the bootstrap configuration

    device.template_context['FOS'] = device.FOS  # FOS version as long integer, like 6_000_013 for '6.0.13'
    device.template_context['mgmt'] = device.mgmt  # mgmt info (interface, vlanid, ipmask)
    # device.template_context['mgmt_fpoc'] = device.mgmt_fpoc_ip  # e.g., 172.16.31.254
    device.template_context['mgmt_gw'] = poc.mgmt_gw
    device.template_context['mgmt_dns'] = poc.mgmt_dns
    device.template_context['mgmt_vrf'] = poc.mgmt_vrf
    device.template_context['apiadmin'] = device.apiadmin
    device.template_context['HA'] = device.ha

    # No need to pass the 'request' (which adds CSRF tokens) since this is a rendering for FGT CLI settings
    device.config = loader.render_to_string(f'{RELPATH_FPOC_BOOTSTRAP_CONFIGS}/{device.model}_{device.fos_version}.conf',
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

    return not is_running_bootstrap(device)  # Returns False if FGT is not running bootstrap config, True otherwise.


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


def deploy(poc: TypePoC, device: FortiGate):
    """
    Render the configuration (Jinja2 template) and deploy it to the FGT

    :param poc:
    :param device:
    :return:
    """

    # Prepare the FGT: API admin, API key and FortiOS version
    #
    if poc.request.POST.get('previewOnly') and poc.request.POST.get('targetedFOSversion'):
        device.fos_version = poc.request.POST['targetedFOSversion']  # FOS version assigned to FGTs for config rendering
    else:
        prepare_api(device)  # create API admin and key if needed
        # ensure FGT runs the desired FortiOS version if user asked for a specific FOS version
        prepare_fortios_version(device, fos_version_target=poc.request.POST['targetedFOSversion'],
                                FOS_minimum=poc.minimum_FOS_version,
                                lock=poc.lock)

    # Special PoC which only uploads bootstrap config to the FGT
    #
    if poc.id == 0:
        render_bootstrap_config(poc, device)
        if not poc.request.POST.get('previewOnly'):
            upload_bootstrap_config(device)  # for this PoC, the bootstrap config is pushed unconditionally, without
            # checking if there is a bootstrap config already running on the FGT. This is because there are different
            # possible options for the bootstrap config (e.g., 'WAN_underlays')
            # It's simpler to push the bootstrap config unconditionally than having to check whether the bootstrap
            # config running on the FGT has the same options as the ones requested

        save_config(poc.__class__.__name__, device, 0)  # Save the bootstrap config
        raise CompletedDeviceProcessing

    # Render the config (CLI script or full-config)
    # Upload bootstrap config (if CLI script)
    # Deploy the config (CLI script of full-config)
    #

    # Add information to the template context of this device
    device.template_context['fos_version'] = device.fos_version  # FOS version encoded as a string like '6.0.13'
    device.template_context['FOS'] = device.FOS  # FOS version as long integer, like 6_000_013 for '6.0.13'
    # device.template_context['mgmt_fpoc'] = device.mgmt_fpoc_ip  # 172.16.31.254
    device.template_context['mgmt_gw'] = poc.mgmt_gw
    device.template_context['mgmt_dns'] = poc.mgmt_dns
    device.template_context['mgmt_vrf'] = poc.mgmt_vrf
    device.template_context['HA'] = device.ha
    device.template_context['wan'] = device.wan

    # No need to pass the 'request' (which adds CSRF tokens) since this is a rendering for FGT CLI settings
    # device.config = loader.render_to_string(f'fpoc/{poc.__class__.__name__}/poc{poc.id:02}/{device.template_group}/{device.template_filename}',
    #                                         device.template_context, using='jinja2')
    device.config = loader.render_to_string(f'fpoc/{poc.template_folder}/poc{poc.id:02}/{device.template_group}/{device.template_filename}',
                                            device.template_context, using='jinja2')
    # print(cli_settings)

    # if the config is not a full-config: Upload bootstrap config to FGT (if it is not running one)
    if not poc.request.POST.get('previewOnly') and is_config_snippets(device.config) and should_upload_boostrap(device):
        render_bootstrap_config(poc, device)
        upload_bootstrap_config(device)
        save_config(poc.__class__.__name__, device, 0)  # Save the bootstrap config
        if device.ha.mode == FortiGate_HA.Modes.FGCP and device.ha.role == FortiGate_HA.Roles.SECONDARY:
            raise CompletedDeviceProcessing
        else:
            device.apikey = None  # reset cached API key since there is no API key in the bootstrap config
            raise ReProcessDevice(sleep=120)  # Leave enough time for the FGT to load the config and reboot

    # Save this CLI configuration to disk
    save_config(poc.__class__.__name__, device, poc.id)

    # Deploy the config
    if poc.request.POST.get('previewOnly'):  # Only preview of the config is requested, no deployment needed
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
