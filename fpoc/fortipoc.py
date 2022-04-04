import threading

class FortiPoC:
    BASE_PORT_SSH = 11000  # SSH ports for FortiPoC devices are 10100 + poc-devid: 10101, 10102, 10103, ...
    BASE_PORT_HTTPS = 14000  # HTTPS ports for FortiPoC devices are 10400 + poc-devid: 10401, 10402, 10403, ...
    mgmt_fpoc_ipmask = '172.16.31.254/24'  # mgmt IP@ of FortiPoC in its OOB management subnet
    # manager_inside_fpoc: bool
    # ip: str  # e.g '172.16.31.254'  IP@ used by fpoc-manager to access the FortiPoC VM
    # it is the mgmt_fpoc IP@ when the fpoc-manager runs inside the FortiPoC VM
    # lock: threading.Lock  # mutual exclusion (mutex) lock which can be used for concurrency (e.g., download FOS firmware)
    devices: dict

    # Dict[DeviceHint]

    def __iter__(self):
        """"
        Makes the class an iterable which can iterate over the devices stored in the 'devices' dictionary
        Leverage the iterator from 'devices' iterable
        """
        return iter(self.devices.values())

    @classmethod
    @property
    def name(cls):
        """
        Return the name of the Class itself
        """
        return cls.__name__
