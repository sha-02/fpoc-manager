from fpoc import FortiGate, Interface, WAN
from fpoc.PoC_SDWAN import FabricStudioSDWAN

# List of devices that is imported by once.py to build the class
# devices = {
#     'HUB1': FabricStudioSDWAN.devices['WEST-DC1'],
#     'HUB2': FabricStudioSDWAN.devices['WEST-DC2'],
#     'BRANCH1': FabricStudioSDWAN.devices['WEST-BR1'],
#     'BRANCH2': FabricStudioSDWAN.devices['WEST-BR2'],
#     'BRANCH3': FabricStudioSDWAN.devices['EAST-BR1'],
# }

devices = {
    'HUB1': FortiGate(offset=0, nameid='fgt000', name_phy='HUB1',
                          mgmt=Interface('port10', 0, '172.16.31.11/24'),
                          lan=Interface('port5', 0, ''),
                          wan=WAN(
                              inet1=Interface('port1', 0, '100.64.11.1/24', 'Internet_1'),
                              inet2=Interface('port2', 0, '100.64.12.1/24', 'Internet_2'),
                              inet3=Interface('port3', 0, '100.64.13.1/24', 'Internet_3'),
                              mpls1=Interface('port4', 0, '10.71.14.1/24', 'MPLS'),
                          )),

    'HUB2': FortiGate(offset=2, nameid='fgt001', name_phy='HUB2',
                          mgmt=Interface('port10', 0, '172.16.31.21/24'),
                          lan=Interface('port5', 0, ''),
                          wan=WAN(
                              inet1=Interface('port1', 0, '100.64.21.1/24', 'Internet_1'),
                              inet2=Interface('port2', 0, '100.64.22.1/24', 'Internet_2'),
                              inet3=Interface('port3', 0, '100.64.23.1/24', 'Internet_3'),
                              mpls1=Interface('port4', 0, '10.71.24.1/24', 'MPLS'),
                          )),

    'BRANCH1': FortiGate(offset=4, nameid='fgt002', name_phy='BR1',
                          mgmt=Interface('port10', 0, '172.16.31.31/24'),
                          lan=Interface('port5', 0, ''),
                          wan=WAN(
                              inet1=Interface('port1', 0, '100.64.41.1/24', 'Internet_1'),
                              inet2=Interface('port2', 0, '100.64.42.1/24', 'Internet_2'),
                              inet3=Interface('port3', 0, '100.64.43.1/24', 'Internet_3'),
                              mpls1=Interface('port4', 0, '10.71.44.1/24', 'MPLS'),
                          )),

    'BRANCH2': FortiGate(offset=6, nameid='fgt003', name_phy='BR2',
                          mgmt=Interface('port10', 0, '172.16.31.41/24'),
                          lan=Interface('port5', 0, ''),
                          wan=WAN(
                              inet1=Interface('port1', 0, '100.64.51.1/24', 'Internet_1'),
                              inet2=Interface('port2', 0, '100.64.52.1/24', 'Internet_2'),
                              inet3=Interface('port3', 0, '100.64.53.1/24', 'Internet_3'),
                              mpls1=Interface('port4', 0, '10.71.54.1/24', 'MPLS'),
                          )),

    'BRANCH3': FortiGate(offset=7, nameid='fgt005', name_phy='BR3',
                          mgmt=Interface('port10', 0, '172.16.31.42/24'),
                          lan=Interface('port5', 0, ''),
                          wan=WAN(
                              inet1=Interface('port1', 0, '100.64.61.1/24', 'Internet_1'),
                              inet2=Interface('port2', 0, '100.64.62.1/24', 'Internet_2'),
                              inet3=Interface('port3', 0, '100.64.63.1/24', 'Internet_3'),
                              mpls1=Interface('port4', 0, '10.71.64.1/24', 'MPLS'),
                          )),

    'BRANCH4': FortiGate(offset=5, nameid='fgt009', name_phy='BR4',
                          mgmt=Interface('port10', 0, '172.16.31.3/24'),
                          lan=Interface('port5', 0, ''),
                          wan=WAN(
                              inet1=Interface('port1', 0, '100.64.71.1/24', 'Internet_1'),
                              inet2=Interface('port2', 0, '100.64.72.1/24', 'Internet_2'),
                              inet3=Interface('port3', 0, '100.64.73.1/24', 'Internet_3'),
                              mpls1=Interface('port4', 0, '10.71.74.1/24', 'MPLS'),
                          )),

    'INFRACOM': FortiGate(offset=1, nameid='fgt006', name_phy='INFRACOM',
                          mgmt=Interface('port10', 0, '172.16.31.1/24'),
                          ),
}
