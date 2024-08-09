from django.core.handlers.wsgi import WSGIRequest
from fpoc import FortiLab, FortiGate, WAN, Interface, Network


class FortiLabSDWAN(FortiLab):
    """
    """
    template_folder = 'FortiPoCSDWAN'
    mgmt_gw = '10.210.1.254'      # Gateway for OOB mgmt network
    mgmt_dns = '96.45.45.45'     # DNS from the OOB mgmt
    mpls_summary = '10.71.0.0/16'
    devices = {
        # SDW-1001F-A
        'WEST-DC1': FortiGate(name='WEST-DC1', name_fpoc='SDW-1001F-A', model='FGT_1001F', password='fortinet',
                            offset=0, mgmt=Interface('mgmt', 0, '10.210.0.50/23'),
                            lan=Interface('port5', 0, ''),
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
                                mpls1=Interface('port2', 14, '10.71.14'),
                                mpls2=Interface('port2', 15, '10.71.15')
                            )),

        # 'FGT-A_sec': FortiGate(offset=1, mgmt=Interface('port10', 0, '172.16.31.12/24'),
        #                        Interface('port5', 0, ''),
        #                        wan=WAN(
        #                            inet=Interface('port1', 0, '198.51.100'),
        #                            inet1=Interface('port1', 111, '100.64.111'),
        #                            inet2=Interface('port1', 112, '100.64.112'),
        #                            inet3=Interface('port1', 113, '100.64.113'),
        #                            inet_snat=Interface('port1', 200, '192.168.200'),
        #                            inet_dnat=Interface('port1', 201, '192.168.201'),
        #                            inet1_snat=Interface('port1', 210, '192.168.210'),
        #                            inet1_dnat=Interface('port1', 211, '192.168.211'),
        #                            inet2_snat=Interface('port1', 220, '192.168.220'),
        #                            inet2_dnat=Interface('port1', 221, '192.168.221'),
        #                            inet3_snat=Interface('port1', 230, '192.168.230'),
        #                            inet3_dnat=Interface('port1', 231, '192.168.231'),
        #                            mpls1=Interface('port2', 114, '10.71.114'),
        #                            mpls2=Interface('port2', 115, '10.71.115')
        #                            )),

        # SDW-1001F-B
        'WEST-DC2': FortiGate(name='WEST-DC2', name_fpoc='SDW-1001F-B', model='FGT_1001F', password='fortinet',
                            offset=2, mgmt=Interface('mgmt', 0, '10.210.0.59/23'),
                            lan=Interface('port5', 0, ''),
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
                                mpls1=Interface('port2', 24, '10.71.24'),
                                mpls2=Interface('port2', 25, '10.71.25')
                            )),

        # SDW-3301E-A
        'EAST-DC': FortiGate(name='EAST-DC', name_fpoc='SDW-3301E-A', model='FGT_3301E', password='fortinet',
                            offset=3, mgmt=Interface('mgmt1', 0, '10.210.0.63/23'),
                            lan=Interface('port5', 0, ''),
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
                                mpls2=Interface('port2', 125, '10.71.125')
                            )),

        # SDW-101F-A
        'WEST-BR1': FortiGate(name='WEST-BR1', name_fpoc='SDW-101F-A', model='FGT_101F', password='fortinet',
                            offset=4, mgmt=Interface('port10', 0, '10.210.0.23/23'),
                            lan=Interface('port5', 0, ''),
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
                                mpls1=Interface('port2', 34, '10.71.34'),
                                mpls2=Interface('port2', 35, '10.71.35')
                            )),

        # 'FGT-C_sec': FortiGate(offset=5, mgmt=Interface('port10', 0, '172.16.31.32/24'),
        #                        Interface('port5', 0, ''),
        #                        wan=WAN(
        #                            inet=Interface('port1', 0, '192.0.2'),
        #                            inet1=Interface('port1', 131, '100.64.131'),
        #                            inet2=Interface('port1', 132, '100.64.132'),
        #                            inet3=Interface('port1', 133, '100.64.133'),
        #                            inet_snat=Interface('port1', 200, '192.168.200'),
        #                            inet_dnat=Interface('port1', 201, '192.168.201'),
        #                            inet1_snat=Interface('port1', 210, '192.168.210'),
        #                            inet1_dnat=Interface('port1', 211, '192.168.211'),
        #                            inet2_snat=Interface('port1', 220, '192.168.220'),
        #                            inet2_dnat=Interface('port1', 221, '192.168.221'),
        #                            inet3_snat=Interface('port1', 230, '192.168.230'),
        #                            inet3_dnat=Interface('port1', 231, '192.168.231'),
        #                            mpls1=Interface('port2', 134, '10.71.134'),
        #                            mpls2=Interface('port2', 135, '10.71.135')
        #                            )),

        # SDW-101F-B
        'WEST-BR2': FortiGate(name='WEST-BR2', name_fpoc='SDW-101F-B', model='FGT_101F', password='fortinet',
                            offset=6, mgmt=Interface('mgmt', 0, '1.1.1.1/23'),
                            lan=Interface('port5', 0, ''),
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
                                mpls1=Interface('port2', 44, '10.71.44'),
                                mpls2=Interface('port2', 45, '10.71.45')
                            )),

        # SDW-3301E-B
        'EAST-BR': FortiGate(name='EAST-BR', name_fpoc='SDW-3301E-B', model='FGT_3301E', password='fortinet',
                            offset=7, mgmt=Interface('mgmt1', 0, '10.210.0.67/23'),
                            lan=Interface('port5', 0, ''),
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
                                mpls2=Interface('port2', 145, '10.71.145')
                            )),

        # 'PC-WEST-DC1': LXC(offset=11, mgmt=Interface('eth9', 0, '172.16.31.111/24')),
        # 'PC_A2': LXC(offset=12, mgmt=Interface('eth9', 0, '172.16.31.112/24')),
        # 'PC-WEST-DC2': LXC(offset=13, mgmt=Interface('eth9', 0, '172.16.31.121/24')),
        # 'PC-EAST-DC': LXC(offset=14, mgmt=Interface('eth9', 0, '172.16.31.122/24')),
        # 'PC-WEST-BR1': LXC(offset=15, mgmt=Interface('eth9', 0, '172.16.31.131/24')),
        # 'PC_C2': LXC(offset=16, mgmt=Interface('eth9', 0, '172.16.31.132/24')),
        # 'PC-WEST-BR2': LXC(offset=17, mgmt=Interface('eth9', 0, '172.16.31.141/24')),
        # 'PC-EAST-BR': LXC(offset=18, mgmt=Interface('eth9', 0, '172.16.31.142/24')),
        # 'INTERNET-SERVER': LXC(offset=23, mgmt=Interface('eth9', 0, '172.16.31.100/24')),
    }

    def __init__(self, request: WSGIRequest, poc_id: int = 0):
        # Go up the parent chain to store the WSGI request, merge class-level devices with instance-level devices
        # and configure device access info (from within fortipoc or from fortipoc public IP)
        super(FortiLabSDWAN, self).__init__(request, poc_id)

        # Add MPLS summary subnet to each FortiGate
        for device in self.devices.values():
            if isinstance(device, FortiGate) and device.wan is not None:
                device.wan.mpls_summary = Network(self.__class__.mpls_summary)
