from django.core.handlers.wsgi import WSGIRequest
from fpoc import FortiPoC, FortiGate, LXC, VyOS, WAN, Interface, Network


class FortiPoCFoundation1(FortiPoC):
    """
    """
    template_folder = 'FortiPoCFoundation1'
    mpls_summary = '10.71.0.0/16'
    devices = {
        'FGT-A': FortiGate(offset=0, mgmt=Interface('port10', 0, '172.16.31.11/24'),
                           wan=WAN(
                               inet=Interface('port1', 0, '198.51.100'),
                               inet1=Interface('port1', 11, '100.64.11'),
                               inet2=Interface('port1', 12, '100.64.12'),
                               inet3=Interface('port1', 13, '100.64.13'),
                               inet_snat=Interface('port1', 200, '192.168.200'),
                               inet_dnat=Interface('port1', 201, '192.168.201'),
                               inet1_snat=Interface('port1', 210, '192.168.210'),
                               inet1_dnat=Interface('port1', 211, '192.168.211'),
                               inet2_snat=Interface('port1', 220, '192.168.220'),
                               inet2_dnat=Interface('port1', 221, '192.168.221'),
                               inet3_snat=Interface('port1', 230, '192.168.230'),
                               inet3_dnat=Interface('port1', 231, '192.168.231'),
                               mpls1=Interface('port2', 14, '10.71.14'), mpls2=Interface('port2', 15, '10.71.15'))),

        'FGT-A_sec': FortiGate(offset=1, mgmt=Interface('port10', 0, '172.16.31.12/24'),
                               wan=WAN(
                                   inet=Interface('port1', 0, '198.51.100'),
                                   inet1=Interface('port1', 111, '100.64.111'),
                                   inet2=Interface('port1', 112, '100.64.112'),
                                   inet3=Interface('port1', 113, '100.64.113'),
                                   inet_snat=Interface('port1', 200, '192.168.200'),
                                   inet_dnat=Interface('port1', 201, '192.168.201'),
                                   inet1_snat=Interface('port1', 210, '192.168.210'),
                                   inet1_dnat=Interface('port1', 211, '192.168.211'),
                                   inet2_snat=Interface('port1', 220, '192.168.220'),
                                   inet2_dnat=Interface('port1', 221, '192.168.221'),
                                   inet3_snat=Interface('port1', 230, '192.168.230'),
                                   inet3_dnat=Interface('port1', 231, '192.168.231'),
                                   mpls1=Interface('port2', 114, '10.71.114'),
                                   mpls2=Interface('port2', 115, '10.71.115'))),

        'FGT-B': FortiGate(offset=2, mgmt=Interface('port10', 0, '172.16.31.21/24'),
                           wan=WAN(
                               inet=Interface('port1', 0, '203.0.113'),
                               inet1=Interface('port1', 21, '100.64.21'),
                               inet2=Interface('port1', 22, '100.64.22'),
                               inet3=Interface('port1', 23, '100.64.23'),
                               inet_snat=Interface('port1', 200, '192.168.200'),
                               inet_dnat=Interface('port1', 201, '192.168.201'),
                               inet1_snat=Interface('port1', 210, '192.168.210'),
                               inet1_dnat=Interface('port1', 211, '192.168.211'),
                               inet2_snat=Interface('port1', 220, '192.168.220'),
                               inet2_dnat=Interface('port1', 221, '192.168.221'),
                               inet3_snat=Interface('port1', 230, '192.168.230'),
                               inet3_dnat=Interface('port1', 231, '192.168.231'),
                               mpls1=Interface('port2', 24, '10.71.24'), mpls2=Interface('port2', 25, '10.71.25'))),

        'FGT-B_sec': FortiGate(offset=3, mgmt=Interface('port10', 0, '172.16.31.22/24'),
                               wan=WAN(
                                   inet=Interface('port1', 0, '203.0.113'),
                                   inet1=Interface('port1', 121, '100.64.121'),
                                   inet2=Interface('port1', 122, '100.64.122'),
                                   inet3=Interface('port1', 123, '100.64.123'),
                                   inet_snat=Interface('port1', 200, '192.168.200'),
                                   inet_dnat=Interface('port1', 201, '192.168.201'),
                                   inet1_snat=Interface('port1', 210, '192.168.210'),
                                   inet1_dnat=Interface('port1', 211, '192.168.211'),
                                   inet2_snat=Interface('port1', 220, '192.168.220'),
                                   inet2_dnat=Interface('port1', 221, '192.168.221'),
                                   inet3_snat=Interface('port1', 230, '192.168.230'),
                                   inet3_dnat=Interface('port1', 231, '192.168.231'),
                                   mpls1=Interface('port2', 124, '10.71.124'),
                                   mpls2=Interface('port2', 125, '10.71.125'))),

        'FGT-C': FortiGate(offset=4, mgmt=Interface('port10', 0, '172.16.31.31/24'),
                           wan=WAN(
                               inet=Interface('port1', 0, '192.0.2'),
                               inet1=Interface('port1', 31, '100.64.31'),
                               inet2=Interface('port1', 32, '100.64.32'),
                               inet3=Interface('port1', 33, '100.64.33'),
                               inet_snat=Interface('port1', 200, '192.168.200'),
                               inet_dnat=Interface('port1', 201, '192.168.201'),
                               inet1_snat=Interface('port1', 210, '192.168.210'),
                               inet1_dnat=Interface('port1', 211, '192.168.211'),
                               inet2_snat=Interface('port1', 220, '192.168.220'),
                               inet2_dnat=Interface('port1', 221, '192.168.221'),
                               inet3_snat=Interface('port1', 230, '192.168.230'),
                               inet3_dnat=Interface('port1', 231, '192.168.231'),
                               mpls1=Interface('port2', 34, '10.71.34'), mpls2=Interface('port2', 35, '10.71.35'))),

        'FGT-C_sec': FortiGate(offset=5, mgmt=Interface('port10', 0, '172.16.31.32/24'),
                               wan=WAN(
                                   inet=Interface('port1', 0, '192.0.2'),
                                   inet1=Interface('port1', 131, '100.64.131'),
                                   inet2=Interface('port1', 132, '100.64.132'),
                                   inet3=Interface('port1', 133, '100.64.133'),
                                   inet_snat=Interface('port1', 200, '192.168.200'),
                                   inet_dnat=Interface('port1', 201, '192.168.201'),
                                   inet1_snat=Interface('port1', 210, '192.168.210'),
                                   inet1_dnat=Interface('port1', 211, '192.168.211'),
                                   inet2_snat=Interface('port1', 220, '192.168.220'),
                                   inet2_dnat=Interface('port1', 221, '192.168.221'),
                                   inet3_snat=Interface('port1', 230, '192.168.230'),
                                   inet3_dnat=Interface('port1', 231, '192.168.231'),
                                   mpls1=Interface('port2', 134, '10.71.134'),
                                   mpls2=Interface('port2', 135, '10.71.135'))),

        'FGT-D': FortiGate(offset=6, mgmt=Interface('port10', 0, '172.16.31.41/24'),
                           wan=WAN(
                               inet=Interface('port1', 0, '100.64.40'),
                               inet1=Interface('port1', 41, '100.64.41'),
                               inet2=Interface('port1', 42, '100.64.42'),
                               inet3=Interface('port1', 43, '100.64.43'),
                               inet_snat=Interface('port1', 200, '192.168.200'),
                               inet_dnat=Interface('port1', 201, '192.168.201'),
                               inet1_snat=Interface('port1', 210, '192.168.210'),
                               inet1_dnat=Interface('port1', 211, '192.168.211'),
                               inet2_snat=Interface('port1', 220, '192.168.220'),
                               inet2_dnat=Interface('port1', 221, '192.168.221'),
                               inet3_snat=Interface('port1', 230, '192.168.230'),
                               inet3_dnat=Interface('port1', 231, '192.168.231'),
                               mpls1=Interface('port2', 44, '10.71.44'), mpls2=Interface('port2', 45, '10.71.45'))),

        'FGT-D_sec': FortiGate(offset=7, mgmt=Interface('port10', 0, '172.16.31.42/24'),
                               wan=WAN(
                                   inet=Interface('port1', 0, '100.64.40'),
                                   inet1=Interface('port1', 141, '100.64.141'),
                                   inet2=Interface('port1', 142, '100.64.142'),
                                   inet3=Interface('port1', 143, '100.64.143'),
                                   inet_snat=Interface('port1', 200, '192.168.200'),
                                   inet_dnat=Interface('port1', 201, '192.168.201'),
                                   inet1_snat=Interface('port1', 210, '192.168.210'),
                                   inet1_dnat=Interface('port1', 211, '192.168.211'),
                                   inet2_snat=Interface('port1', 220, '192.168.220'),
                                   inet2_dnat=Interface('port1', 221, '192.168.221'),
                                   inet3_snat=Interface('port1', 230, '192.168.230'),
                                   inet3_dnat=Interface('port1', 231, '192.168.231'),
                                   mpls1=Interface('port2', 144, '10.71.144'),
                                   mpls2=Interface('port2', 145, '10.71.145'))),

        'ISFW-A': FortiGate(offset=8, mgmt=Interface('port10', 0, '172.16.31.13/24')),
        'Internet': VyOS(offset=9, mgmt=Interface('eth9', 0, '172.16.31.251/24')),
        'MPLS': VyOS(offset=10, mgmt=Interface('eth9', 0, '172.16.31.252/24')),
        'PC_A1': LXC(offset=11, mgmt=Interface('eth9', 0, '172.16.31.111/24')),
        'PC_A2': LXC(offset=12, mgmt=Interface('eth9', 0, '172.16.31.112/24')),
        'PC_B1': LXC(offset=13, mgmt=Interface('eth9', 0, '172.16.31.121/24')),
        'PC_B2': LXC(offset=14, mgmt=Interface('eth9', 0, '172.16.31.122/24')),
        'PC_C1': LXC(offset=15, mgmt=Interface('eth9', 0, '172.16.31.131/24')),
        'PC_C2': LXC(offset=16, mgmt=Interface('eth9', 0, '172.16.31.132/24')),
        'PC_D1': LXC(offset=17, mgmt=Interface('eth9', 0, '172.16.31.141/24')),
        'PC_D2': LXC(offset=18, mgmt=Interface('eth9', 0, '172.16.31.142/24')),
        'RTR-NAT_A': LXC(offset=19, mgmt=Interface('eth9', 0, '172.16.31.10/24')),
        'RTR-NAT_B': LXC(offset=20, mgmt=Interface('eth9', 0, '172.16.31.20/24')),
        'RTR-NAT_C': LXC(offset=21, mgmt=Interface('eth9', 0, '172.16.31.30/24')),
        'RTR-NAT_D': LXC(offset=22, mgmt=Interface('eth9', 0, '172.16.31.40/24')),
        'SRV_INET': LXC(offset=23, mgmt=Interface('eth9', 0, '172.16.31.100/24')),
        'WAN_Controller': LXC(offset=24, mgmt=Interface('eth9', 0, '172.16.31.250/24'))
    }

    # def __init__(self, request: WSGIRequest, poc_id: int = 0, devices: dict = None, fpoc_devnames: list = None):
    def __init__(self, request: WSGIRequest, poc_id: int = 0):
        # Go up the parent chain to store the WSGI request, merge class-level devices with instance-level devices
        # and configure device access info (from within fortipoc or from fortipoc public IP)
        super(FortiPoCFoundation1, self).__init__(request, poc_id)

        # Add MPLS summary subnet to each FortiGate
        for device in self.devices.values():
            if isinstance(device, FortiGate) and device.wan is not None:
                device.wan.mpls_summary = Network(self.__class__.mpls_summary)
