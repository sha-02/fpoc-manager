from django.core.handlers.wsgi import WSGIRequest

# from http.client import RemoteDisconnected
# from netmiko import NetmikoTimeoutException
# from urllib3.exceptions import TimeoutError
# from requests.exceptions import Timeout, ConnectionError

import time
import datetime
import threading

import fpoc.fortios as fortios
import fpoc.lxc as lxc
import fpoc.vyos as vyos
from fpoc import TypePoC, TypeDevice, FortiGate, LXC, Vyos, FortiManager
from fpoc import CompletedDeviceProcessing, StopProcessingDevice, ReProcessDevice, AbortDeployment


def start_poc(request: WSGIRequest, poc: TypePoC, device_dependencies: dict) -> list:
    """

    :param request: request.POST contains, among other things, the devices to be started for this poc
    :param poc: contains all the devices defined for this poc
    :param device_dependencies:
    :return:
    """

    # the intersection of the keys of request.POST dict and the keys of poc.devices dict produces the keys of each
    # device to be started for this poc. Also add the keys of the device dependencies.
    dev_keys_to_start = set()
    for devkey in request.POST.keys() & poc.devices.keys():
        dev_keys_to_start.add(devkey)  # add the device key
        dev_keys_to_start.update(device_dependencies.get(devkey, set()))  # update with the tuples listed in device_dependencies

    # {devkey: devices[devkey] for devkey in dev_keys_to_start}
    # +--> do not use dict comprehension because it creates an unordered list of devices due to using set()
    # Delete devices from 'devices' which do not need to be started
    # for devkey in poc.devices.copy():  # use a copy otherwise an exception is raised because the dict changes size
    for devkey in list(poc.devices.keys()):  # use list of keys() otherwise exception raised bcse the dict changes size
        # during iteration
        if devkey not in dev_keys_to_start:
            del (poc.devices[devkey])  # this device was not requested to be started for this PoC

    start_time = time.perf_counter()
    deploy_configs(request, poc)
    end_time = time.perf_counter()

    duration_seconds = end_time - start_time
    print(f'\n\nDeployment finished. It took {datetime.timedelta(seconds=duration_seconds)}.\n')

    # List of all config settings rendered from template
    status_devices = [
        {'name': device.name, 'name_fpoc': device.name_fpoc,
         'deployment_status': device.deployment_status,
         'URL': device_URL(request, poc, device),
         'context': device.template_context, 'config': device.config} for device in poc]

    return status_devices


def device_URL(request: WSGIRequest, poc: TypePoC, device: TypeDevice) -> str:
    """
    returns URL to access the device via the FortiPoC
    """
    ip = request.headers['Host'].split(':')[0] if poc.manager_inside_fpoc else device.ip

    if isinstance(device, FortiGate) or isinstance(device, FortiManager):
        return f'https://{ip}:{poc.BASE_PORT_HTTPS + device.offset}/'
    if isinstance(device, LXC) or isinstance(device, Vyos):
        return f'https://{ip}/term/dev_{device.name_fpoc}/ssh'

    return f'https://0.0.0.0:0'  # dummy URL (should not reach this code)


def deploy_configs(request: WSGIRequest, poc: TypePoC, multithread=True):
    """
    Deploy the configurations to all devices

    :param request:
    :param poc:
    :param multithread:
    :return:
    """
    if multithread:
        threads = list()
        for device in poc:
            thread = threading.Thread(target=deploy_config, args=(request, poc, device))
            threads.append(thread)
            thread.start()

        for index, thread in enumerate(threads):
            thread.join()
    else:
        for device in poc:
            deploy_config(request, poc, device)


def deploy_config(request: WSGIRequest, poc: TypePoC, device: TypeDevice):
    """
    Deploy the configuration for a device

    """
    print('=' * 50, f'{device.name} : Processing device', '=' * 50)
    nb_failures = 0

    while True:  # a device may require multiple deployment attempts
        try:
            deploy(request, poc, device)

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

        except AbortDeployment:
            print('Aborting deployment !')
            return None

        # except (ConnectionError, Timeout, TimeoutError, RemoteDisconnected, NetmikoTimeoutException) as ex:
        except Exception as ex:
            nb_failures += 1
            if nb_failures >= 5:
                print(f'\n{device.name} : *** ERROR ***', ex, f' *** limit of 5 failures is reached, '
                                                              ' device is skipped ***\n\n')  # display message
                device.deployment_status = 'skipped'
                break  # exit the 'while True' loop to process the next device

            print(f'\n{device.name} : error - ', ex,
                  f'\n{device.name} : Waiting for 15 seconds before re-processing device ...')
            time.sleep(15)
            print(f'{device.name} : Processing device once again')  # before reprocessing the device

        else:  # No exception occurred for this device
            print(f'{device.name} : Finished processing device')
            device.deployment_status = 'completed'
            break  # exit the 'while True' loop to process the next device


def deploy(request: WSGIRequest, poc: TypePoC, device: TypeDevice):
    """
    Render the configuration (Django template) and deploy it to the device

    :param request:
    :param poc:
    :param device:
    :return:
    """

    if isinstance(device, FortiGate):
        fortios.deploy(request, poc, device)
    elif isinstance(device, LXC):
        lxc.deploy(request, poc, device)
    elif isinstance(device, Vyos):
        vyos.deploy(request, poc, device)
    elif isinstance(device, FortiManager):
        pass    # Nothing to deploy on FMG
    else:
        raise StopProcessingDevice(f'{device.name} : the type of this device is not supported for deployment')
