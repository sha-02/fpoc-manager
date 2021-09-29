# Create your tests here.

# class FortiOSversion:
#     """ Data Descriptor Class to manage FortiOS version """
#     def __set_name__(self, owner_class, property_name):
#         self.property_name = property_name
#
#     def __set__(self, instance, fos_version):
#         self.fos_version = fos_version
#
#         try:
#             major, minor, patch = fos_version.split('.')
#             if int(major) < 1 or int(minor) < 0 or int(patch) < 0:
#                 raise ValueError
#         except: # catch all exceptions
#             print(f'Incorrect FortiOS version')
#             raise   # propagate the exception
#
#         self.fos_version_hexadecimal = int('0x' + ''.join([string.hexdigits[int(major)],
#                                                            string.hexdigits[int(minor)],
#                                                            string.hexdigits[int(patch)]]))
#         instance.__dict__[self.property_name] = 'toto'
#
#     def __get__(self, instance, owner_class):
#         if instance is None:
#             return self
#         else:
#             return instance.__dict__.get(self.property_name, None)
#
#
# class FGT:
#     fos = FortiOSversion()
#
# fgt = FGT()
# fgt.fos = '6.0.11'
#
# temp = '6.0.11'.split('.')
# a,b,c = temp
#
# h = string.hexdigits
#
# pass

# @dataclass
# class FGT:
#     fos_version: str = None
#
#     # @property
#     # def FOS(self):  # hexadecimal integer of the fos_version, e.g. "6.0.13" returns 0x60D
#     #     major, minor, patch = self.fos_version.split('.')
#     #     return int(''.join([string.hexdigits[int(major)], string.hexdigits[int(minor)], string.hexdigits[int(patch)]]), 16)
#
#     @property
#     def FOS(self):  # long integer of the fos_version, e.g. "6.0.13" returns 6_000_013 (used for django template)
#         major, minor, patch = self.fos_version.split('.')
#         return int(major)*1_000_000 + int(minor)*1_000 + int(patch)
#
# fgt = FGT()
#
# fgt.fos_version = "6.0.13"
#
# # print(f"hexa= {fgt.FOS:#0x}")
# print(f"decimal= {fgt.FOS:_}")
#
# pass

#############################################

# import netmiko
# import re
# from netmiko import NetmikoAuthenticationException
#
# ssh_params = {
#     'ip': '10.5.55.10',
#     'username': 'admin',
#     'password': 'fortinet',
#     'device_type': 'linux',
#     'port': 22,
#     # 'verbose': True,
#     # 'conn_timeout': 1,
#     # 'auth_timeout': 1,
#     # 'banner_timeout': 1,
#     # 'blocking_timeout': 1,
#     # 'timeout': 1,
#     # 'session_timeout': 1,
#     # 'auto_connect': True,
# }
#
# # SSH connection to the FGT
# try:
#     ssh = netmiko.ConnectHandler(**ssh_params)
# except NetmikoAuthenticationException:
#     print('SSH authentication failed. Retrying with empty password.')
#     ssh_params['password'] = ''
#     ssh = netmiko.ConnectHandler(**ssh_params)
#
# # output = ssh.send_command('poc device list')
# # print(output)
#
# output = ssh.send_command('poc device license ISFW-A')
# print(output)

#############################################

# from pathlib import Path
# from config.settings import BASE_DIR
#
# print(Path(__file__))
# print(Path(__file__).resolve())
# print(Path(__file__).resolve().parent.parent)
# print(BASE_DIR)

##############################################

import datetime
import threading
import time

devices = ['FGT-A', 'FGT-B', 'FGT-C']


def deploy(device: str, i: int):
    """
    """
    # if i == 1:
    #     return

    if i <= 5:
        print(f'{device} processing number {i}')
        time.sleep(1)
        raise UserWarning

    if i > 5:
        raise StopIteration


def deploy_config(device: str):
    """
    """
    i = 1
    print(f'{device} : starting')
    while True:
        try:
            deploy(device, i)
        except UserWarning:  # re-process device
            i = i + 1
            print(f'{device} : re-processing')

        except StopIteration:
            print(f'{device} : stopped processing by exception')
            break
        else:
            print(f'{device} : completed without exception')
            break


def deploy_configs(devices: list, multithread=True):
    """
    """
    if multithread:
        threads = list()
        for device in devices:
            thread = threading.Thread(target=deploy_config, args=(device,))
            threads.append(thread)
            thread.start()

        for index, thread in enumerate(threads):
            thread.join()
    else:
        for device in devices:
            deploy_config(device)


start_time = time.perf_counter()
deploy_configs(devices)
end_time = time.perf_counter()
duration_seconds = end_time - start_time
print(f'\n\nDeployment finished. It took {datetime.timedelta(seconds=duration_seconds)}.\n')
