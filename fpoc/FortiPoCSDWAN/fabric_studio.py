from django.core.handlers.wsgi import WSGIRequest
from fpoc import FortiPoC, FortiGate, LXC, VyOS, WAN, Interface, Network, FabricStudio


class FabricStudioSDWAN(FabricStudio):
    """
    """
    template_folder = 'FortiPoCSDWAN'
    mpls_summary = '10.71.0.0/16'  # mpls_summary assigned to the WAN of each FGT of this PoC
    password = 'nsefortinet'  # password assigned to each FGT of this PoC

    devices = {
        'WEST-DC1': FortiGate(offset=0, mgmt=Interface('port10', 0, '172.16.31.11/24'),
                            lan=Interface('port5', 0, ''),
                            wan=WAN(
                                inet1=Interface('port1', 0, '100.64.11.1/24', 'Internet_1'),
                                inet2=Interface('port2', 0, '100.64.12.1/24', 'Internet_2'),
                                mpls1=Interface('port3', 0, '10.71.14.1/24', 'MPLS'),
                            )),

        'WEST-DC2': FortiGate(offset=2, mgmt=Interface('port10', 0, '172.16.31.21/24'),
                            lan=Interface('port5', 0, ''),
                            wan=WAN(
                                inet1=Interface('port1', 0, '100.64.21.1/24', 'Internet_1'),
                                inet2=Interface('port2', 0, '100.64.22.1/24', 'Internet_2'),
                                mpls1=Interface('port3', 0, '10.71.24.1/24', 'MPLS'),
                            )),

        'EAST-DC': FortiGate(offset=3, mgmt=Interface('port10', 0, '172.16.31.22/24'),
                            lan=Interface('port5', 0, ''),
                            wan=WAN(
                                inet1=Interface('port1', 0, '100.64.31.1/24', 'Internet_1'),
                                inet2=Interface('port2', 0, '100.64.32.1/24', 'Internet_2'),
                                mpls1=Interface('port3', 0, '10.71.34.1/24', 'MPLS'),
                            )),

        'WEST-BR1': FortiGate(offset=4, mgmt=Interface('port10', 0, '172.16.31.31/24'),
                            lan=Interface('port5', 0, ''),
                            wan=WAN(
                                inet1=Interface('port1', 0, '100.64.41.1/24', 'Internet_1'),
                                inet2=Interface('port2', 0, '100.64.42.1/24', 'Internet_2'),
                                mpls1=Interface('port3', 0, '10.71.44.1/24', 'MPLS'),
                            )),

        'WEST-BR2': FortiGate(offset=6, mgmt=Interface('port10', 0, '172.16.31.41/24'),
                            lan=Interface('port5', 0, ''),
                            wan=WAN(
                                inet1=Interface('port1', 0, '100.64.51.1/24', 'Internet_1'),
                                inet2=Interface('port2', 0, '100.64.52.1/24', 'Internet_2'),
                                mpls1=Interface('port3', 0, '10.71.54.1/24', 'MPLS'),
                            )),

        'EAST-BR': FortiGate(offset=7, mgmt=Interface('port10', 0, '172.16.31.42/24'),
                            lan=Interface('port5', 0, ''),
                            wan=WAN(
                                inet1=Interface('port1', 0, '100.64.61.1/24', 'Internet_1'),
                                inet2=Interface('port2', 0, '100.64.62.1/24', 'Internet_2'),
                                mpls1=Interface('port3', 0, '10.71.64.1/24', 'MPLS'),
                            )),

        'WAN': FortiGate(offset=9, mgmt=Interface('port10', 0, '172.16.31.251/24'),
                            lan=Interface('port5', 0, ''),
                            wan=WAN(
                                inet=Interface('port9', 0, '198.18.8.1/24', 'INTERNET'),
                                inet1=Interface('port1', 0, '203.0.113.254/24', 'ISP1'),
                                inet2=Interface('port2', 0, '198.51.100.254/24', 'ISP2'),
                                mpls1=Interface('port3', 0, '10.71.0.254/24', 'MPLS_SP1'),
                            )),

        # 'PC-WEST-DC1': LXC(offset=11, mgmt=Interface('eth9', 0, '172.16.31.111/24')),
        # 'PC-WEST-DC2': LXC(offset=13, mgmt=Interface('eth9', 0, '172.16.31.121/24')),
        # 'PC-EAST-DC': LXC(offset=14, mgmt=Interface('eth9', 0, '172.16.31.122/24')),
        # 'PC-WEST-BR1': LXC(offset=15, mgmt=Interface('eth9', 0, '172.16.31.131/24')),
        # 'PC-WEST-BR2': LXC(offset=17, mgmt=Interface('eth9', 0, '172.16.31.141/24')),
        # 'PC-EAST-BR': LXC(offset=18, mgmt=Interface('eth9', 0, '172.16.31.142/24')),
        # 'INTERNET-SERVER': LXC(offset=23, mgmt=Interface('eth9', 0, '172.16.31.100/24')),
    }

    def __init__(self, request: WSGIRequest, poc_id: int = 0):
        # Go up the parent chain to store the WSGI request, merge class-level devices with instance-level devices
        # and configure device access info (from within fortipoc or from fortipoc public IP)
        super(FabricStudioSDWAN, self).__init__(request, poc_id)

        # Add password and MPLS summary subnet to each FortiGate
        for device in self.devices.values():
            if isinstance(device, FortiGate):
                device.password = self.password
                if device.wan is not None:
                    device.wan.mpls_summary = Network(self.mpls_summary)
