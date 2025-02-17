from django.core.handlers.wsgi import WSGIRequest
from fpoc import FortiLab, FortiGate, WAN, Interface, Network

# Define each FGT appliance in the hardware Lab

SDW_1001F_A = FortiGate(name_fpoc='SDW-1001F-A', alias='SDW-1001F-A', model='FGT_1001F', password='fortinet',
                            npu='NP7', reboot_delay=300,
                            mgmt=Interface('mgmt', 0, '10.210.0.59/23'),
                            lan=Interface('port6', vlanid=0, speed='1000auto'),
                            wan=WAN(
                                inet1=Interface('port1', vlanid=0, speed='1000auto'),
                                inet2=Interface('port2', vlanid=0, speed='1000auto'),
                                mpls1=Interface('port4', vlanid=0, speed='1000auto'),
                            ))

SDW_1001F_B = FortiGate(name_fpoc='SDW-1001F-B', alias='SDW-1001F-B', model='FGT_1001F', password='fortinet',
                            npu='NP7', reboot_delay=300,
                            mgmt=Interface('mgmt', 0, '10.210.0.50/23'),
                            lan=Interface('port6', vlanid=0, speed='1000auto'),
                            wan=WAN(
                                inet1=Interface('port1', vlanid=0, speed='1000auto'),
                                inet2=Interface('port2', vlanid=0, speed='1000auto'),
                                mpls1=Interface('port4', vlanid=0, speed='1000auto'),
                            ))

SDW_3301E_A = FortiGate(name_fpoc='SDW-3301E-A', alias='SDW-3301E-A', model='FGT_3301E', password='fortinet',
                            npu='NP6', reboot_delay=300,
                            mgmt=Interface('mgmt1', 0, '10.210.0.63/23'),
                            lan=Interface('port22', vlanid=0, speed='1000full'),
                            wan=WAN(
                                inet1=Interface('port17', vlanid=0, speed='1000full'),
                                inet2=Interface('port18', vlanid=0, speed='1000full'),
                                mpls1=Interface('port20', vlanid=0, speed='1000full'),
                            ))

SDW_3301E_B = FortiGate(name_fpoc='SDW-3301E-B', alias='SDW-3301E-B', model='FGT_3301E', password='fortinet',
                            npu='NP6', reboot_delay=300,
                            mgmt=Interface('mgmt1', 0, '10.210.0.67/23'),
                            lan=Interface('port22', vlanid=0, speed='1000full'),
                            wan=WAN(
                                inet1=Interface('port17', vlanid=0, speed='1000full'),
                                inet2=Interface('port18', vlanid=0, speed='1000full'),
                                mpls1=Interface('port20', vlanid=0, speed='1000full'),
                            ))

SDW_101F_A = FortiGate(name_fpoc='SDW-101F-A', alias='SDW-101F-A', model='FGT_101F', password='fortinet',
                            npu='SoC4', reboot_delay=180,
                            mgmt=Interface('mgmt', 0, '10.210.0.23/23'),
                            lan=Interface('port4', vlanid=0, speed='auto'),
                            wan=WAN(
                                inet1=Interface('wan1', vlanid=0, speed='auto'),
                                inet2=Interface('port1', vlanid=0, speed='auto'),
                                mpls1=Interface('port2', vlanid=0, speed='auto'),
                            ))

SDW_101F_B = FortiGate(name_fpoc='SDW-101F-B', alias='SDW-101F-B', model='FGT_101F', password='fortinet',
                            npu='SoC4', reboot_delay=180,
                            mgmt=Interface('mgmt', 0, '10.210.0.41/23'),
                            lan=Interface('port4', vlanid=0, speed='auto'),
                            wan=WAN(
                                inet1=Interface('port1', vlanid=0, speed='auto'),
                                inet2=Interface('port2', vlanid=0, speed='auto'),
                                mpls1=Interface('wan1', vlanid=0, speed='auto'),
                            ))


# Define each role for the PoC

WEST_DC1 = FortiGate(name='WEST-DC1',
                            wan=WAN(
                                inet1=Interface(address='100.64.11.1/24'),
                                inet2=Interface(address='100.64.12.1/24'),
                                mpls1=Interface(address='10.71.14.1/24'),
                            ))

WEST_DC2 = FortiGate(name='WEST-DC2',
                            wan=WAN(
                                inet1=Interface(address='100.64.21.2/24'),
                                inet2=Interface(address='100.64.22.2/24'),
                                mpls1=Interface(address='10.71.24.2/24'),
                            ))

EAST_DC = FortiGate(name='EAST-DC',
                            wan=WAN(
                                inet1=Interface(address='100.64.51.3/24'),
                                inet2=Interface(address='100.64.52.3/24'),
                                mpls1=Interface(address='10.71.54.3/24'),
                            ))

EAST_BR = FortiGate(name='EAST-BR',
                            wan=WAN(
                                inet1=Interface(address='dhcp'),
                                inet2=Interface(address='dhcp'),
                                mpls1=Interface(address='dhcp'),
                            ))

WEST_BR1 = FortiGate(name='WEST-BR1',
                            wan=WAN(
                                inet1=Interface(address='dhcp'),
                                inet2=Interface(address='dhcp'),
                                mpls1=Interface(address='dhcp'),
                            ))

WEST_BR2 = FortiGate(name='WEST-BR2',
                            wan=WAN(
                                inet1=Interface(address='dhcp'),
                                inet2=Interface(address='dhcp'),
                                mpls1=Interface(address='dhcp'),
                            ))

# Define which physical FGT is assigned which role

WEST_DC1.update(SDW_1001F_A)
WEST_DC2.update(SDW_1001F_B)

WEST_BR1.update(SDW_101F_A)
WEST_BR2.update(SDW_101F_B)

EAST_DC.update(SDW_3301E_A)
EAST_BR.update(SDW_3301E_B)


class FortiLabSDWAN(FortiLab):
    """
    """
    template_folder = 'FortiPoCSDWAN'
    mgmt_gw = '10.210.1.254'      # Gateway for OOB mgmt network
    mgmt_dns = '96.45.45.45'     # DNS from the OOB mgmt
    mgmt_vrf = 10
    mpls_summary = '10.71.0.0/16'  # mpls_summary assigned to the WAN of each FGT of this PoC

    devices = {
        'WEST-DC1': WEST_DC1,
        'WEST-DC2': WEST_DC2,
        'EAST-DC': EAST_DC,
        'WEST-BR1': WEST_BR1,
        'WEST-BR2': WEST_BR2,
        'EAST-BR': EAST_BR,
    }

    def __init__(self, request: WSGIRequest, poc_id: int = 0):
        # Go up the parent chain to store the WSGI request, merge class-level devices with instance-level devices
        # and configure device access info
        super(FortiLabSDWAN, self).__init__(request, poc_id)

        # Add MPLS summary subnet to each FortiGate
        for device in self.devices.values():
            if isinstance(device, FortiGate) and device.wan is not None:
                device.wan.mpls_summary = Network(self.__class__.mpls_summary)
