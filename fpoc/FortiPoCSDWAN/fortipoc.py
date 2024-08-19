from django.core.handlers.wsgi import WSGIRequest
from fpoc import FortiPoC, FortiGate, LXC, VyOS, WAN, Interface, Network


class FortiPoCSDWAN(FortiPoC):
    """
    """
    template_folder = 'FortiPoCSDWAN'
    mpls_summary = '10.71.0.0/16'  # mpls_summary assigned to the WAN of each FGT of this PoC
    password = 'nsefortinet'  # password assigned to each FGT of this PoC

    devices = {
        'WEST-DC1': FortiGate(offset=0, mgmt=Interface('port10', 0, '172.16.31.11/24'),
                            lan=Interface('port5', 0, ''),
                            wan=WAN(
                                inet1=Interface('port1', 11, '100.64.11.1/24', 'Internet_1'),
                                inet2=Interface('port1', 12, '100.64.12.1/24', 'Internet_2'),
                                mpls1=Interface('port2', 14, '10.71.14.1/24', 'MPLS'),
                            )),

        'WEST-DC2': FortiGate(offset=2, mgmt=Interface('port10', 0, '172.16.31.21/24'),
                            lan=Interface('port5', 0, ''),
                            wan=WAN(
                                inet1=Interface('port1', 21, '100.64.21.2/24', 'Internet_1'),
                                inet2=Interface('port1', 22, '100.64.22.2/24', 'Internet_2'),
                                mpls1=Interface('port2', 24, '10.71.24.2/24', 'MPLS'),
                            )),

        'EAST-DC': FortiGate(offset=3, mgmt=Interface('port10', 0, '172.16.31.22/24'),
                            lan=Interface('port5', 0, ''),
                            wan=WAN(
                                inet1=Interface('port1', 121, '100.64.121.3/24', 'Internet_1'),
                                inet2=Interface('port1', 122, '100.64.122.3/24', 'Internet_2'),
                                mpls1=Interface('port2', 124, '10.71.124.3/24', 'MPLS'),
                            )),

        'WEST-BR1': FortiGate(offset=4, mgmt=Interface('port10', 0, '172.16.31.31/24'),
                            lan=Interface('port5', 0, ''),
                            wan=WAN(
                                inet1=Interface('port1', 31, 'dhcp', 'Internet_1'),
                                inet2=Interface('port1', 32, 'dhcp', 'Internet_2'),
                                mpls1=Interface('port2', 34, '10.71.34.1/24', 'MPLS'),
                            )),

        'WEST-BR2': FortiGate(offset=6, mgmt=Interface('port10', 0, '172.16.31.41/24'),
                            lan=Interface('port5', 0, ''),
                            wan=WAN(
                                inet1=Interface('port1', 41, 'dhcp', 'Internet_1'),
                                inet2=Interface('port1', 42, 'dhcp', 'Internet_2'),
                                mpls1=Interface('port2', 44, '10.71.44.2/24', 'MPLS'),
                            )),

        'EAST-BR': FortiGate(offset=7, mgmt=Interface('port10', 0, '172.16.31.42/24'),
                            lan=Interface('port5', 0, ''),
                            wan=WAN(
                                inet1=Interface('port1', 141, 'dhcp', 'Internet_1'),
                                inet2=Interface('port1', 142, 'dhcp', 'Internet_2'),
                                mpls1=Interface('port2', 144, '10.71.144.3/24', 'MPLS'),
                            )),

        # 'ISFW-A': FortiGate(offset=8, mgmt=Interface('port10', 0, '172.16.31.13/24')),
        # 'Internet': VyOS(offset=9, mgmt=Interface('eth9', 0, '172.16.31.251/24')),
        # 'MPLS': VyOS(offset=10, mgmt=Interface('eth9', 0, '172.16.31.252/24')),
        'PC-WEST-DC1': LXC(offset=11, mgmt=Interface('eth9', 0, '172.16.31.111/24')),
        # 'PC_A2': LXC(offset=12, mgmt=Interface('eth9', 0, '172.16.31.112/24')),
        'PC-WEST-DC2': LXC(offset=13, mgmt=Interface('eth9', 0, '172.16.31.121/24')),
        'PC-EAST-DC': LXC(offset=14, mgmt=Interface('eth9', 0, '172.16.31.122/24')),
        'PC-WEST-BR1': LXC(offset=15, mgmt=Interface('eth9', 0, '172.16.31.131/24')),
        # 'PC_C2': LXC(offset=16, mgmt=Interface('eth9', 0, '172.16.31.132/24')),
        'PC-WEST-BR2': LXC(offset=17, mgmt=Interface('eth9', 0, '172.16.31.141/24')),
        'PC-EAST-BR': LXC(offset=18, mgmt=Interface('eth9', 0, '172.16.31.142/24')),
        # 'RTR-NAT_A': LXC(offset=19, mgmt=Interface('eth9', 0, '172.16.31.10/24')),
        # 'RTR-NAT_B': LXC(offset=20, mgmt=Interface('eth9', 0, '172.16.31.20/24')),
        # 'RTR-NAT_C': LXC(offset=21, mgmt=Interface('eth9', 0, '172.16.31.30/24')),
        # 'RTR-NAT_D': LXC(offset=22, mgmt=Interface('eth9', 0, '172.16.31.40/24')),
        'INTERNET-SERVER': LXC(offset=23, mgmt=Interface('eth9', 0, '172.16.31.100/24')),
        # 'WAN_Controller': LXC(offset=24, mgmt=Interface('eth9', 0, '172.16.31.250/24')),
    }

    def __init__(self, request: WSGIRequest, poc_id: int = 0):
        # Go up the parent chain to store the WSGI request, merge class-level devices with instance-level devices
        # and configure device access info (from within fortipoc or from fortipoc public IP)
        super(FortiPoCSDWAN, self).__init__(request, poc_id)

        # Add password and MPLS summary subnet to each FortiGate
        for device in self.devices.values():
            if isinstance(device, FortiGate):
                device.password = self.password
                if device.wan is not None:
                    device.wan.mpls_summary = Network(self.mpls_summary)
