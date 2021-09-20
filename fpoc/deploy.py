from django.core.handlers.wsgi import WSGIRequest

# from http.client import RemoteDisconnected
# from netmiko import NetmikoTimeoutException
# from urllib3.exceptions import TimeoutError
# from requests.exceptions import Timeout, ConnectionError

from time import sleep, perf_counter
from datetime import timedelta

import fpoc.fortios as fortios
import fpoc.lxc as lxc
import fpoc.vyos as vyos
from fpoc.exceptions import CompletedDeviceProcessing, StopProcessingDevice, ReProcessDevice, AbortDeployment
from fpoc.fortipoc import TypePoC, TypeDevice
from fpoc.devices import FortiGate, LXC, Vyos


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
        dev_keys_to_start.update(device_dependencies[devkey])  # update with the tuples listed in device_dependencies

    # {devkey: devices[devkey] for devkey in dev_keys_to_start}
    # +--> do not use dict comprehension because it creates an unordered list of devices due to using set()
    # Delete devices from 'devices' which do not need to be started
    # for devkey in poc.devices.copy():  # use a copy otherwise an exception is raised because the dict changes size
    for devkey in list(poc.devices.keys()):  # use list of keys() otherwise exception raised bcse the dict changes size
        # during iteration
        if devkey not in dev_keys_to_start:
            del (poc.devices[devkey])  # this device was not requested to be started for this PoC

    start_time = perf_counter()
    deploy_configs(request, poc)
    end_time = perf_counter()

    duration_seconds = end_time - start_time
    print(f'\n\nDeployment finished. It took {timedelta(seconds=duration_seconds)}.\n')

    # List of all config settings rendered from template
    status_devices = [
        { 'name': device.name, 'deployment_status': device.deployment_status,
          'ip': request.headers['Host'].split(':')[0] if poc.manager_inside_fpoc else device.ip,
          'https': poc.BASE_PORT_HTTPS + device.offset if poc.manager_inside_fpoc else device.https_port,
          'context': device.template_context, 'config': device.config} for device in poc ]

    return status_devices


def deploy_configs(request: WSGIRequest, poc: TypePoC):
    """
    Deploy the configurations for a scenario to all devices

    :param request:
    :param poc:
    :return:
    """
    for device in poc:
        print('=' * 50, f'Processing {device.name}', '=' * 50)
        nb_failures = 0

        while True:  # a device may require multiple deployment attempts
            try:
                deploy_config(request, poc, device)

            except CompletedDeviceProcessing:
                print(f'Finished processing {device.name}')
                device.deployment_status = 'completed'
                break  # exit the 'while True' loop to process the next device

            except StopProcessingDevice as ex:
                print('\n*** WARNING ***', ex, f' *** {device.name} is skipped ***\n\n')  # display warning message
                device.deployment_status = 'skipped'
                break  # exit the 'while True' loop to process the next device

            except ReProcessDevice as ex:
                if ex.sleep:  # the caller of the exception asks for a sleep delay
                    print(f"Waiting for {ex.sleep} seconds...")
                    sleep(ex.sleep)
                print(f'Processing {device.name} once again')  # before reprocessing the device

            except AbortDeployment:
                print('Aborting deployment !')
                return None

            # except (ConnectionError, Timeout, TimeoutError, RemoteDisconnected, NetmikoTimeoutException) as ex:
            #     nb_failures += 1
            #     if nb_failures > 3:
            #         print('\n*** ERROR ***', ex, f' *** {device.name} is skipped ***\n\n')  # display warning message
            #         break  # exit the 'while True' loop to process the next device
            #
            #     print('\n*** Connection error *** ', ex,
            #           f'\nWaiting for 15 seconds before re-processing {device.name} ...')
            #     sleep(5)
            #     print(f'Processing {device.name} once again')  # before reprocessing the device
            #
            # except Exception as ex:
            #     print('\n*** ERROR ***', ex, f' *** {device.name} is skipped ***\n\n')  # display an error message
            #     break  # exit the 'while True' loop to process the next device

            except Exception as ex:
                nb_failures += 1
                if nb_failures >= 5:
                    print('\n*** ERROR ***', ex, f' *** limit of 5 failures is reached, '
                                                 f' {device.name} is skipped ***\n\n')  # display message
                    break  # exit the 'while True' loop to process the next device

                print('\nerror - ', ex, f'\nWaiting for 15 seconds before re-processing {device.name} ...')
                sleep(15)
                print(f'Processing {device.name} once again')  # before reprocessing the device

            else:  # No exception occurred for this device
                print(f'Finished processing {device.name}')
                device.deployment_status = 'completed'
                break  # exit the 'while True' loop to process the next device


def deploy_config(request: WSGIRequest, poc: TypePoC, device: TypeDevice):
    """
    Render the configuration (Django template) and deploy it to the device

    :param request:
    :param poc_id:
    :param device:
    :return:
    """

    if isinstance(device, FortiGate):
        fortios.deploy_config(request, poc, device)
    elif isinstance(device, LXC):
        lxc.deploy_config(request, poc, device)
    elif isinstance(device, Vyos):
        vyos.deploy_config(request, poc, device)
    else:
        raise StopProcessingDevice(f'{device.name} : the type of this device is not supported for deployment')
