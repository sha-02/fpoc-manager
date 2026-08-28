from fpoc.devices import FortiGate, FortiGate_HA, Interface, LAN, WAN
from fpoc.agora import SDW_agora

# HA on HUB1
# devices_agora = {
#     'HUB1': SDW_agora['SDW_1001F_A']['impairment'],
#     'HUB1-B': SDW_agora['SDW_1001F_B']['impairment'],
#     'HUB2': SDW_agora['SDW_3301E_A']['impairment'],
#     'BRANCH1': SDW_agora['SDW_50G_A']['impairment'],
#     'BRANCH1-B': SDW_agora['SDW_50G_B']['impairment'],
#     'BRANCH2': SDW_agora['SDW_3301E_B']['impairment'],
#     'BRANCH3': SDW_agora['SDW_101F_A']['impairment'],
#     'BRANCH4': SDW_agora['SDW_101F_B']['impairment'],
#     }

# no HA on HUB1
devices_agora = {
    'HUB1': SDW_agora['SDW_1001F_A']['impairment'],
    'HUB2': SDW_agora['SDW_1001F_B']['impairment'],

    'BRANCH1': SDW_agora['SDW_50G_A']['impairment'],
    'BRANCH1-B': SDW_agora['SDW_50G_B']['impairment'],
    'BRANCH2': SDW_agora['SDW_3301E_A']['impairment'],
    'BRANCH3': SDW_agora['SDW_101F_A']['impairment'],
    'BRANCH4': SDW_agora['SDW_101F_B']['impairment'],

    'INFRACOM': FortiGate(model="FGT_VM64_KVM", name_phy='INFRACOM',
                          mgmt=Interface('port1', 0, '172.16.31.102/24'),
                          lan=Interface('port4'),
                          wan=WAN(inet1=Interface('port2'), inet2=Interface('port3'))
                          ),
    }


devices_fabric_studio = {
    'HUB1': FortiGate(offset=0, nameid='fgt000', name_phy='HUB1',
                      mgmt=Interface('port10', 0, '172.16.31.11/24'),
                      HA=FortiGate_HA(mode=FortiGate_HA.Modes.FGCP, role=FortiGate_HA.Roles.PRIMARY,
                                      group_id=91, group_name="HUB1", priority=129,
                                      hbdev=[('port6', 0)], sessyncdev=['port7'],
                                      monitordev=['port1', 'port2', 'port3', 'port5']),
                      lan=Interface('port5', 0),
                      segments=LAN(
                          lan1=Interface('port5', 0),
                          lan2=Interface('port5', 15),
                          lan3=Interface('port5', 16),
                          lan4=Interface('port5', 17),
                      ),
                      wan=WAN(
                          inet1=Interface('port1', 0, '100.64.11.1/24', alias='Internet_1'),
                          inet2=Interface('port2', 0, '100.64.12.1/24', alias='Internet_2'),
                          inet3=Interface('port3', 0, '100.64.13.1/24', alias='Internet_3'),
                          mpls1=Interface('port4', 0, '10.71.14.1/24', alias='MPLS'),
                      )),

    'HUB1-B': FortiGate(offset=3, nameid='fgt004', name_phy='HUB1-B',
                        mgmt=Interface('port10', 0, '172.16.31.22/24'),
                        HA=FortiGate_HA(mode=FortiGate_HA.Modes.FGCP, role=FortiGate_HA.Roles.SECONDARY,
                                        group_id=91, group_name="HUB1", priority=127,
                                        hbdev=[('port6', 0)], sessyncdev=['port7'],
                                        monitordev=['port1', 'port2', 'port3', 'port5'])
                        ),

    'HUB2': FortiGate(offset=2, nameid='fgt001', name_phy='HUB2',
                      mgmt=Interface('port10', 0, '172.16.31.21/24'),
                      lan=Interface('port5', 0),
                      segments=LAN(
                          lan1=Interface('port5', 0),
                          lan2=Interface('port5', 25),
                          lan3=Interface('port5', 26),
                          lan4=Interface('port5', 27),
                      ),
                      wan=WAN(
                              inet1=Interface('port1', 0, '100.64.21.1/24', alias='Internet_1'),
                              inet2=Interface('port2', 0, '100.64.22.1/24', alias='Internet_2'),
                              inet3=Interface('port3', 0, '100.64.23.1/24', alias='Internet_3'),
                              mpls1=Interface('port4', 0, '10.71.24.1/24', alias='MPLS'),
                          )),

    'BRANCH1': FortiGate(offset=4, nameid='fgt002', name_phy='BR1',
                        mgmt=Interface('port10', 0, '172.16.31.31/24'),
                        HA=FortiGate_HA(mode=FortiGate_HA.Modes.FGCP, role=FortiGate_HA.Roles.PRIMARY,
                                     group_id=1, group_name="BRANCH1", priority=129,
                                     hbdev=[('port6', 0)], sessyncdev=['port7'],
                                     monitordev=['port1', 'port2', 'port3', 'port5']),
                        lan=Interface('port5', 0),
                         segments=LAN(
                             lan1=Interface('port5', 0),
                             lan2=Interface('port5', 36),
                             lan3=Interface('port5', 37),
                         ),
                         wan=WAN(
                          inet1=Interface('port1', 0, '100.64.41.1/24', alias='Internet_1'),
                          inet2=Interface('port2', 0, '100.64.42.1/24', alias='Internet_2'),
                          inet3=Interface('port3', 0, '100.64.43.1/24', alias='Internet_3'),
                          mpls1=Interface('port4', 0, '10.71.44.1/24', alias='MPLS'),
                        )),

    'BRANCH1-B': FortiGate(offset=22, nameid='fgt008', name_phy='BR1-B',
                        mgmt=Interface('port10', 0, '172.16.31.32/24'),
                        HA=FortiGate_HA(mode=FortiGate_HA.Modes.FGCP, role=FortiGate_HA.Roles.SECONDARY,
                                       group_id=1, group_name="BRANCH1", priority=127,
                                       hbdev=[('port6', 0)], sessyncdev=['port7'],
                                       monitordev=['port1', 'port2', 'port3', 'port5'])
                           ),

    'BRANCH2': FortiGate(offset=6, nameid='fgt003', name_phy='BR2',
                          mgmt=Interface('port10', 0, '172.16.31.41/24'),
                          lan=Interface('port5', 0),
                         segments=LAN(
                             lan1=Interface('port5', 0),
                             lan2=Interface('port5', 46),
                             lan3=Interface('port5', 47),
                         ),
                         wan=WAN(
                              inet1=Interface('port1', 0, '100.64.51.1/24', alias='Internet_1'),
                              inet2=Interface('port2', 0, '100.64.52.1/24', alias='Internet_2'),
                              inet3=Interface('port3', 0, '100.64.53.1/24', alias='Internet_3'),
                              mpls1=Interface('port4', 0, '10.71.54.1/24', alias='MPLS'),
                          )),

    'BRANCH3': FortiGate(offset=7, nameid='fgt005', name_phy='BR3',
                          mgmt=Interface('port10', 0, '172.16.31.42/24'),
                          lan=Interface('port5', 0),
                         segments=LAN(
                             lan1=Interface('port5', 0),
                             lan2=Interface('port5', 66),
                             lan3=Interface('port5', 67),
                         ),
                         wan=WAN(
                              inet1=Interface('port1', 0, '100.64.61.1/24', alias='Internet_1'),
                              inet2=Interface('port2', 0, '100.64.62.1/24', alias='Internet_2'),
                              inet3=Interface('port3', 0, '100.64.63.1/24', alias='Internet_3'),
                              mpls1=Interface('port4', 0, '10.71.64.1/24', alias='MPLS'),
                          )),

    'BRANCH4': FortiGate(offset=5, nameid='fgt009', name_phy='BR4',
                        mgmt=Interface('port10', 0, '172.16.31.3/24'),
                        lan=Interface('port5', 0),
                        segments=LAN(
                            lan1=Interface('port5', 0),
                            lan2=Interface('port5', 76),
                            lan3=Interface('port5', 77),
                        ),
                        wan=WAN(
                            inet1=Interface('port1', 0, '100.64.71.1/24', alias='Internet_1'),
                            inet2=Interface('port2', 0, '100.64.72.1/24', alias='Internet_2'),
                            inet3=Interface('port3', 0, '100.64.73.1/24', alias='Internet_3'),
                            mpls1=Interface('port4', 0, '10.71.74.1/24', alias='MPLS'),
                        )),

    'INFRACOM': FortiGate(offset=1, nameid='fgt006', name_phy='INFRACOM',
                          mgmt=Interface('port10', 0, '172.16.31.1/24'),
                          lan=Interface('port5'),
                          wan=WAN(inet1=Interface('port1'), inet2=Interface('port2'))
                          ),
    }
