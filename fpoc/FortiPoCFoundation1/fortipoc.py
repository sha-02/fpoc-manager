from django.core.handlers.wsgi import WSGIRequest
from fpoc import FortiPoC, FortiGate, LXC, VyOS, WAN, Interface, Network


class FortiPoCFoundation1(FortiPoC):
    """
    """
    template_folder = 'FortiPoCFoundation1'
    password = 'nsefortinet'  # password assigned to each FGT of this PoC

    devices = {
        'FGT-A': FortiGate(offset=0, mgmt=Interface('port10', 0, '172.16.31.11/24'),
                           lan=Interface('port5', 0, ''),
                           wan=WAN(
                               inet=Interface('port1', 0, '198.51.100.1/24', 'Internet'),
                               inet1=Interface('port1', 11, '100.64.11.1/24', 'Internet_1'),
                               inet2=Interface('port1', 12, '100.64.12.1/24', 'Internet_2'),
                               inet3=Interface('port1', 13, '100.64.13.1/24', 'Internet_3'),
                               inet_snat=Interface('port1', 200, '192.168.200.1/24'),
                               inet_dnat=Interface('port1', 201, '192.168.201.1/24'),
                               inet1_snat=Interface('port1', 210, '192.168.210.1/24'),
                               inet1_dnat=Interface('port1', 211, '192.168.211.1/24'),
                               inet2_snat=Interface('port1', 220, '192.168.220.1/24'),
                               inet2_dnat=Interface('port1', 221, '192.168.221.1/24'),
                               inet3_snat=Interface('port1', 230, '192.168.230.1/24'),
                               inet3_dnat=Interface('port1', 231, '192.168.231.1/24'),
                               mpls1=Interface('port2', 14, '10.71.14.1/24'),
                               mpls2=Interface('port2', 15, '10.71.15.1/24'))),

        'FGT-A_sec': FortiGate(offset=1, mgmt=Interface('port10', 0, '172.16.31.12/24'),
                               lan=Interface('port5', 0, ''),
                               wan=WAN(
                                   inet=Interface('port1', 0, '198.51.100.2/24', 'Internet'),
                                   inet1=Interface('port1', 111, '100.64.111.2/24', 'Internet_1'),
                                   inet2=Interface('port1', 112, '100.64.112.2/24', 'Internet_2'),
                                   inet3=Interface('port1', 113, '100.64.113.2/24', 'Internet_3'),
                                   inet_snat=Interface('port1', 200, '192.168.200.2/24'),
                                   inet_dnat=Interface('port1', 201, '192.168.201.2/24'),
                                   inet1_snat=Interface('port1', 210, '192.168.210.2/24'),
                                   inet1_dnat=Interface('port1', 211, '192.168.211.2/24'),
                                   inet2_snat=Interface('port1', 220, '192.168.220.2/24'),
                                   inet2_dnat=Interface('port1', 221, '192.168.221.2/24'),
                                   inet3_snat=Interface('port1', 230, '192.168.230.2/24'),
                                   inet3_dnat=Interface('port1', 231, '192.168.231.2/24'),
                                   mpls1=Interface('port2', 114, '10.71.114.2/24'),
                                   mpls2=Interface('port2', 115, '10.71.115.2/24'))),

        'FGT-B': FortiGate(offset=2, mgmt=Interface('port10', 0, '172.16.31.21/24'),
                           lan=Interface('port5', 0, ''),
                           wan=WAN(
                               inet=Interface('port1', 0, '203.0.113.1/24', 'Internet'),
                               inet1=Interface('port1', 21, '100.64.21.1/24', 'Internet_1'),
                               inet2=Interface('port1', 22, '100.64.22.1/24', 'Internet_2'),
                               inet3=Interface('port1', 23, '100.64.23.1/24', 'Internet_3'),
                               inet_snat=Interface('port1', 200, '192.168.200.1/24'),
                               inet_dnat=Interface('port1', 201, '192.168.201.1/24'),
                               inet1_snat=Interface('port1', 210, '192.168.210.1/24'),
                               inet1_dnat=Interface('port1', 211, '192.168.211.1/24'),
                               inet2_snat=Interface('port1', 220, '192.168.220.1/24'),
                               inet2_dnat=Interface('port1', 221, '192.168.221.1/24'),
                               inet3_snat=Interface('port1', 230, '192.168.230.1/24'),
                               inet3_dnat=Interface('port1', 231, '192.168.231.1/24'),
                               mpls1=Interface('port2', 24, '10.71.24.1/24'),
                               mpls2=Interface('port2', 25, '10.71.25.1/24'))),

        'FGT-B_sec': FortiGate(offset=3, mgmt=Interface('port10', 0, '172.16.31.22/24'),
                               lan=Interface('port5', 0, ''),
                               wan=WAN(
                                   inet=Interface('port1', 0, '203.0.113.2/24', 'Internet'),
                                   inet1=Interface('port1', 121, '100.64.121.2/24', 'Internet_1'),
                                   inet2=Interface('port1', 122, '100.64.122.2/24', 'Internet_2'),
                                   inet3=Interface('port1', 123, '100.64.123.2/24', 'Internet_3'),
                                   inet_snat=Interface('port1', 200, '192.168.200.2/24'),
                                   inet_dnat=Interface('port1', 201, '192.168.201.2/24'),
                                   inet1_snat=Interface('port1', 210, '192.168.210.2/24'),
                                   inet1_dnat=Interface('port1', 211, '192.168.211.2/24'),
                                   inet2_snat=Interface('port1', 220, '192.168.220.2/24'),
                                   inet2_dnat=Interface('port1', 221, '192.168.221.2/24'),
                                   inet3_snat=Interface('port1', 230, '192.168.230.2/24'),
                                   inet3_dnat=Interface('port1', 231, '192.168.231.2/24'),
                                   mpls1=Interface('port2', 124, '10.71.124.2/24', 'MPLS'),
                                   mpls2=Interface('port2', 125, '10.71.125.2/24', 'MPLS_2'))),

        'FGT-C': FortiGate(offset=4, mgmt=Interface('port10', 0, '172.16.31.31/24'),
                           lan=Interface('port5', 0, ''),
                           wan=WAN(
                               inet=Interface('port1', 0, '192.0.2.1/24', 'Internet'),
                               inet1=Interface('port1', 31, '100.64.31.1/24', 'Internet_1'),
                               inet2=Interface('port1', 32, '100.64.32.1/24', 'Internet_2'),
                               inet3=Interface('port1', 33, '100.64.33.1/24', 'Internet_3'),
                               inet_snat=Interface('port1', 200, '192.168.200.1/24'),
                               inet_dnat=Interface('port1', 201, '192.168.201.1/24'),
                               inet1_snat=Interface('port1', 210, '192.168.210.1/24'),
                               inet1_dnat=Interface('port1', 211, '192.168.211.1/24'),
                               inet2_snat=Interface('port1', 220, '192.168.220.1/24'),
                               inet2_dnat=Interface('port1', 221, '192.168.221.1/24'),
                               inet3_snat=Interface('port1', 230, '192.168.230.1/24'),
                               inet3_dnat=Interface('port1', 231, '192.168.231.1/24'),
                               mpls1=Interface('port2', 34, '10.71.34.1/24', 'MPLS'),
                               mpls2=Interface('port2', 35, '10.71.35.1/24', 'MPLS_2'))),

        'FGT-C_sec': FortiGate(offset=5, mgmt=Interface('port10', 0, '172.16.31.32/24'),
                               lan=Interface('port5', 0, ''),
                               wan=WAN(
                                   inet=Interface('port1', 0, '192.0.2.2/24', 'Internet'),
                                   inet1=Interface('port1', 131, '100.64.131.2/24', 'Internet_1'),
                                   inet2=Interface('port1', 132, '100.64.132.2/24', 'Internet_2'),
                                   inet3=Interface('port1', 133, '100.64.133.2/24', 'Internet_3'),
                                   inet_snat=Interface('port1', 200, '192.168.200.2/24'),
                                   inet_dnat=Interface('port1', 201, '192.168.201.2/24'),
                                   inet1_snat=Interface('port1', 210, '192.168.210.2/24'),
                                   inet1_dnat=Interface('port1', 211, '192.168.211.2/24'),
                                   inet2_snat=Interface('port1', 220, '192.168.220.2/24'),
                                   inet2_dnat=Interface('port1', 221, '192.168.221.2/24'),
                                   inet3_snat=Interface('port1', 230, '192.168.230.2/24'),
                                   inet3_dnat=Interface('port1', 231, '192.168.231.2/24'),
                                   mpls1=Interface('port2', 134, '10.71.134.2/24', 'MPLS'),
                                   mpls2=Interface('port2', 135, '10.71.135.2/24', 'MPLS_2'))),

        'FGT-D': FortiGate(offset=6, mgmt=Interface('port10', 0, '172.16.31.41/24'),
                           lan=Interface('port5', 0, ''),
                           wan=WAN(
                               inet=Interface('port1', 0, '100.64.40.1/24', 'Internet'),
                               inet1=Interface('port1', 41, '100.64.41.1/24', 'Internet_1'),
                               inet2=Interface('port1', 42, '100.64.42.1/24', 'Internet_2'),
                               inet3=Interface('port1', 43, '100.64.43.1/24', 'Internet_3'),
                               inet_snat=Interface('port1', 200, '192.168.200.1/24'),
                               inet_dnat=Interface('port1', 201, '192.168.201.1/24'),
                               inet1_snat=Interface('port1', 210, '192.168.210.1/24'),
                               inet1_dnat=Interface('port1', 211, '192.168.211.1/24'),
                               inet2_snat=Interface('port1', 220, '192.168.220.1/24'),
                               inet2_dnat=Interface('port1', 221, '192.168.221.1/24'),
                               inet3_snat=Interface('port1', 230, '192.168.230.1/24'),
                               inet3_dnat=Interface('port1', 231, '192.168.231.1/24'),
                               mpls1=Interface('port2', 44, '10.71.44.1/24', 'MPLS'),
                               mpls2=Interface('port2', 45, '10.71.45.1/24', 'MPLS_2'))),

        'FGT-D_sec': FortiGate(offset=7, mgmt=Interface('port10', 0, '172.16.31.42/24'),
                               lan=Interface('port5', 0, ''),
                               wan=WAN(
                                   inet=Interface('port1', 0, '100.64.40.2/24', 'Internet'),
                                   inet1=Interface('port1', 141, '100.64.141.2/24', 'Internet_1'),
                                   inet2=Interface('port1', 142, '100.64.142.2/24', 'Internet_2'),
                                   inet3=Interface('port1', 143, '100.64.143.2/24', 'Internet_3'),
                                   inet_snat=Interface('port1', 200, '192.168.200.2/24'),
                                   inet_dnat=Interface('port1', 201, '192.168.201.2/24'),
                                   inet1_snat=Interface('port1', 210, '192.168.210.2/24'),
                                   inet1_dnat=Interface('port1', 211, '192.168.211.2/24'),
                                   inet2_snat=Interface('port1', 220, '192.168.220.2/24'),
                                   inet2_dnat=Interface('port1', 221, '192.168.221.2/24'),
                                   inet3_snat=Interface('port1', 230, '192.168.230.2/24'),
                                   inet3_dnat=Interface('port1', 231, '192.168.231.2/24'),
                                   mpls1=Interface('port2', 144, '10.71.144.2/24', 'MPLS'),
                                   mpls2=Interface('port2', 145, '10.71.145.2/24', 'MPLS_2'))),

        'ISFW-A': FortiGate(offset=8, mgmt=Interface('port10', 0, '172.16.31.13/24'),
                            lan=Interface(),
                            wan=WAN(
                                inet=Interface(),
                                inet1=Interface(),
                                inet2=Interface(),
                                inet3=Interface(),
                                inet_snat=Interface(),
                                inet_dnat=Interface(),
                                inet1_snat=Interface(),
                                inet1_dnat=Interface(),
                                inet2_snat=Interface(),
                                inet2_dnat=Interface(),
                                inet3_snat=Interface(),
                                inet3_dnat=Interface(),
                                mpls1=Interface(),
                                mpls2=Interface())),

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

        # Add password to each FortiGate
        for device in self.devices.values():
            if isinstance(device, FortiGate):
                device.password = self.password
