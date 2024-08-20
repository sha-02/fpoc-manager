import threading
from django.core.handlers.wsgi import WSGIRequest
import copy
from fpoc.devices import FortiGate


class FortiLab:
    devices: dict = {}  # The class-level dict containing all possible devices which can be used in this poc
    mgmt_gw = None      # Gateway for OOB mgmt network
    mgmt_dns = None     # DNS from the OOB mgmt
    mgmt_vrf = 0        # VRF for the OOB mgmt
    template_folder = None  # Folder hosting the jinja templates


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

    def __init__(self, request: WSGIRequest, poc_id: int = 0):
        """
        Build a poc instances with all the devices
        """
        self.request = request  # The Web request causing the poc creation
        self.id = poc_id
        self.minimum_FOS_version = 0  # Minimum FortiOS version required for the devices of this poc (eg, 7_004_002)
        self.messages = ["<no message>"]  # List of messages regarding this poc which are displayed to the user
        self.lock = threading.Lock()  # mutual exclusion (mutex) lock used for concurrency (e.g., download FOS firmware)

        # Configure default SSH/HTTPS ports for FortiGates
        for device in self.devices.values():
            if isinstance(device, FortiGate):
                device.https_port = 443
                device.ssh_port = 22

    def members(self, devices: dict = None, devnames: list = None):
        """
        Only keep some devices for this poc

        'devices' or 'devnames' provides the list of devices to be configured for the PoC
        This set of device is the same set as the class 'devices' or is a subset of the class 'devices'
        The devices to be configured can be provided in two ways:
        - via 'devices': dict of devices of the form {'devname': FortiGate(...), 'devname': LXC(...), ...}
        - via 'devnames': list of device names

        Each device name (in list 'devnames' or the keys in 'devices' dict) must correspond to a key in
        class 'devices' dictionary.
        """

        # The poc instance self.devices dict can be built from 'devices' or from 'devname'
        # One of them must be passed as argument, not both
        if devices and devnames:
            raise TypeError("'devices' and 'devnames' cannot be both provided")

        #
        # build the dict of all devices needed for this poc: self.devices
        #

        # If no specific device filter is requested then the list of devices for this instance
        # (self.devices) is inherited from its class and contain all devices.
        if devices is None and devnames is None:
            pass  # Nothing to do, self.devices is simply the class devices

        elif devnames:  # Build the poc self.devices dict from the list of poc device name in 'devnames'
            self.devices = {devname: copy.deepcopy(self.__class__.devices[devname]) for devname in devnames}

        elif devices:  # Build the poc self.devices dict from the 'devices' dict
            self.devices = {}
            # "merge" the attributes from a device defined in the Class with its counter-part passed as argument
            for devname, device in devices.items():
                # Retrieve all the device's attributes from the Class
                self.devices[devname] = copy.deepcopy(self.__class__.devices[devname])  # Shallow copy may not be enough
                # Update (Override) with all attributes from the device passed as argument
                # for k, v in device.__dict__.items():
                #     if v is not None:
                #         self.devices[devname].__dict__[k] = v
                self.devices[devname].update(device)

        # set the device IP to its OOB MGMT IP
        for fpoc_devname, device in self.devices.items():
            device.ip = device.mgmt.ip


    @classmethod
    def devices_of_type(cls, device_class) -> dict:
        """
        Return all devices of the same class: for eg, all FortiGates, all LXCes, all VyOSes
        """
        return {devname: copy.deepcopy(device) for devname, device in cls.devices.items()
                if isinstance(device, device_class)}
