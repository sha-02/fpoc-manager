import os, sys

from django.core.handlers.wsgi import WSGIRequest

# from http.client import RemoteDisconnected
# from netmiko import NetmikoTimeoutException
# from urllib3.exceptions import TimeoutError
# from requests.exceptions import Timeout, ConnectionError

import time
import datetime
import threading

from collections import namedtuple
from django.shortcuts import render
from django.http import HttpResponse

import fpoc.fortios as fortios
import fpoc.lxc as lxc
import fpoc.vyos as vyos
from fpoc import TypePoC, TypeDevice, FortiGate, LXC, VyOS
from fpoc import CompletedDeviceProcessing, StopProcessingDevice, ReProcessDevice, AbortDeployment, RetryProcessingDevice


# Status = namedtuple('Status', 'is_valid is_invalid errors')


# def inspect(poc: TypePoC) -> Status:
def inspect(poc: TypePoC) -> list:
    """
    """
    import ipaddress
    errors = []   # List of error messages to return

    for ipaddr in (poc.request.POST.get('fpocIP'),):
        if ipaddr:
            # Ensure a valid IP address is provided
            try:
                ipaddress.ip_address(ipaddr)  # throws an exception if the IP address is not valid
            except:
                # return Status(False, True, f"This is not a valid IP address: {ipaddr}")
                errors.append(f"This is not a valid IP address: {ipaddr}")

    if poc.request.POST.get('previewOnly') and not poc.request.POST.get('targetedFOSversion'):
        # return Status(False, True, 'FOS version must be specified when preview-only is selected')
        errors.append('FOS version must be specified when preview-only is selected')

    if poc.template_folder is None:
        errors.append(f"'template_folder' is not defined in Class '{poc.__class__.__name__}'")

    # if errors:
    #     return Status(False, True, errors)
    # else:
    #     return Status(True, False, errors)
    return errors


# def start(request: WSGIRequest, poc_id: int, devices: dict, class_ ) -> HttpResponse:
def start(poc: TypePoC, devices: dict) -> HttpResponse:

    errors = inspect(poc)
    if errors:
        return render(poc.request, f'fpoc/message.html',
                      {'title': 'Error', 'header': 'Error', 'message': errors})

    if '127.0.0.1' in poc.request.get_host() and poc.request.POST.get('pocInstance')=='0.0.0.0' \
            and poc.request.POST['fpocIP'] == '' \
            and bool(poc.request.POST.get('previewOnly', False)) == False:
        return render(poc.request, f'fpoc/message.html',
                      {'title': 'Error', 'header': 'Error',
                       'message': "Select a PoC instance from the list, 'internal' is not a valid choice from 127.0.0.1"})

    # Create the list of devices which must be used for this PoC
    # devices = copy.deepcopy(devices)

    # the intersection of the keys of request.POST dict and the keys of 'devices' dict produces the keys of each
    # device to be used for this poc.
    fpoc_devnames = poc.request.POST.keys() & devices.keys()

    # Delete devices from 'devices' which do not need to be started
    # +--> do not use dict comprehension because it creates an unordered list of devices due to using set()
    for fpoc_devname in list(devices.keys()):  # use list of keys() otherwise exception raised bcse
        # the dict changes size during iteration
        if fpoc_devname not in fpoc_devnames:
            del(devices[fpoc_devname])  # this device was not requested to be started for this PoC

    # Only keep the 'devices' that are active members for the poc
    poc.members(devices=devices)

    status_devices = start2(poc)

    return render(poc.request, f'fpoc/deployment_status.html',
                  {'poc_id': poc.id, 'devices': status_devices, 'messages': poc.messages})


def start2(poc: TypePoC) -> list:
    """
    :param poc: contains all the devices defined for this poc
    :return:
    """

    start_time = time.perf_counter()
    deploy_configs(poc)
    end_time = time.perf_counter()

    duration_seconds = end_time - start_time
    print(f'\n\nDeployment finished. It took {datetime.timedelta(seconds=duration_seconds)}.\n')

    # List of all config settings rendered from template
    status_devices = [
        {'name': device.name, 'name_fpoc': device.name_fpoc,
         'deployment_status': device.deployment_status,
         'URL': device_URL(poc, device),
         'URL_console': device_URL_console(poc, device),
         'context': device.template_context, 'config': device.config} for device in poc]

    return status_devices


def device_URL(poc: TypePoC, device: TypeDevice) -> tuple:
    """
    returns URL to access the device via the FortiPoC (HTTPS for FGT/FMG, SSH for LXC/VyOS)
    """
    if 'fortipoc' in poc.request.path:
        ip = poc.request.headers['Host'].split(':')[0] if poc.manager_inside_fpoc else device.ip
        if isinstance(device, FortiGate):
            return 'HTTPS', f'https://{ip}:{poc.BASE_PORT_HTTPS + device.offset}/'
        if isinstance(device, LXC) or isinstance(device, VyOS):
            return 'SSH', f'https://{ip}/term/dev_i_{device.offset:02}_{device.name_fpoc}/ssh'

    return 'HTTPS', f'https://{device.mgmt.ip}:{device.https_port}'


def device_URL_console(poc: TypePoC, device: TypeDevice) -> str:
    """
    returns URL to access the device via its FortiPoC console
    """
    if 'fortipoc' in poc.request.path:
        ip = poc.request.headers['Host'].split(':')[0] if poc.manager_inside_fpoc else device.ip
        if isinstance(device, FortiGate) or isinstance(device, VyOS):
            return f'https://{ip}/term/dev_i_{device.offset:02}_{device.name_fpoc}/cons'
        if isinstance(device, LXC):
            return f'https://{ip}/term/dev_i_{device.offset:02}_{device.name_fpoc}/lxcbash'

    return ''  # no console, empty string returned


def deploy_configs(poc: TypePoC, multithread=True):
    """
    Deploy the configurations to all devices

    :param poc:
    :param multithread:
    :return:
    """
    if multithread:
        threads = list()
        for device in poc:
            thread = threading.Thread(target=deploy_config, args=(poc, device))
            threads.append(thread)
            thread.start()

        for index, thread in enumerate(threads):
            thread.join()
    else:
        for device in poc:
            deploy_config(poc, device)


def deploy_config(poc: TypePoC, device: TypeDevice):
    """
    Deploy the configuration for a device

    """
    # print('=' * 50, f'{device.name} : Processing device', '=' * 50)
    print(f'{device.name} : Processing device')
    nb_failures = auth_failures = 0

    while True:  # a device may require multiple deployment attempts
        try:
            deploy(poc, device)

        except CompletedDeviceProcessing:
            print(f'{device.name} : Finished processing')
            device.deployment_status = 'completed'
            break  # exit the 'while True' loop to process the next device

        except StopProcessingDevice as ex:
            print(f'\n{device.name} : *** WARNING ***', ex, ' *** device is skipped ***\n\n')  # display warning message
            device.deployment_status = 'skipped'
            break  # exit the 'while True' loop to process the next device

        except ReProcessDevice as ex:
            if ex.sleep:  # the caller of the exception asks for a sleep delay
                print(f'{device.name} : Waiting for {ex.sleep} seconds...')
                time.sleep(ex.sleep)
            print(f'{device.name} : Processing device once again')  # before reprocessing the device

        except ConnectionResetError:
            print(f'{device.name} : Connection was reset by peer. It\'s probably rebooting. Waiting for {device.reboot_delay} seconds...')
            time.sleep(device.reboot_delay)
            print(f'{device.name} : Processing device once again')  # before reprocessing the device

        except AbortDeployment:
            print('Aborting deployment !')
            return None

        # except (ConnectionError, Timeout, TimeoutError, RemoteDisconnected, NetmikoTimeoutException) as ex:
        except (RetryProcessingDevice, Exception) as ex:
            nb_failures += 1
            if nb_failures >= 5:
                print(f'\n{device.name} : *** ERROR ***', ex, f' *** limit of 5 failures is reached, '
                                                              ' device is skipped ***\n\n')  # display message
                device.deployment_status = 'failed'
                break  # exit the 'while True' loop to process the next device

            print(f'\n{device.name} : error (#{nb_failures}/5)- ', ex)

            # Display detailed information about the exception (class, filename, line number)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

            if isinstance(device, FortiGate) and "401 Unauthorized" in str(ex):
                print(f'\n{device.name} : Authentication failure')
                device.apikey = None
                if device.apiv2auth:
                    auth_failures += 1
                    if auth_failures >= 2 and device.apiv2auth:
                        print(f'\n{device.name} : admin/pwd APIv2 authentication failed twice, trying with API user')
                        device.apiv2auth = False    # Switch to authentication based on API admin (config.system.api-user)

            print(f'\n{device.name} : Waiting for 15 seconds before re-processing device ...')
            time.sleep(15)
            print(f'{device.name} : Processing device once again')  # before reprocessing the device

        else:  # No exception occurred for this device
            print(f'{device.name} : Finished processing device')
            device.deployment_status = 'completed'
            break  # exit the 'while True' loop to process the next device


def deploy(poc: TypePoC, device: TypeDevice):
    """
    Render the configuration (Django template) and deploy it to the device

    :param poc:
    :param device:
    :return:
    """

    if isinstance(device, FortiGate):
        fortios.deploy(poc, device)
    elif isinstance(device, LXC):
        lxc.deploy(poc, device)
    elif isinstance(device, VyOS):
        vyos.deploy(poc, device)
    else:
        raise StopProcessingDevice(f'{device.name} : the type of this device is not supported for deployment')
