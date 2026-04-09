from fpoc import FortiGate, WAN, Interface

# Define each FGT appliance in Agora Hardware Lab

SDW_1001F_A = FortiGate(name_fpoc='SDW-1001F-A', alias='SDW-1001F-A', model='FGT_1001F', password='Fortinet123#',
                            npu='NP7', reboot_delay=300,
                            mgmt=Interface('mgmt', 0, '10.210.0.59/23'),
                            lan=Interface('port6', vlanid=0, speed='1000auto'),
                            wan=WAN(
                                # inet1=Interface('port1', vlanid=0, speed='1000auto'),
                                # inet2=Interface('port2', vlanid=0, speed='1000auto'),
                                # mpls1=Interface('port4', vlanid=0, speed='1000auto'),
                                inet1=Interface('port1', name="Internet_1", vlanid=71, speed='1000auto'),
                                inet2=Interface('port2', name="Internet_2", vlanid=72, speed='1000auto'),
                                mpls1=Interface('port4', name="MPLS", vlanid=74, speed='1000auto'),
                            ))

SDW_1001F_B = FortiGate(name_fpoc='SDW-1001F-B', alias='SDW-1001F-B', model='FGT_1001F', password='Fortinet123#',
                            npu='NP7', reboot_delay=300,
                            mgmt=Interface('mgmt', 0, '10.210.0.50/23'),
                            lan=Interface('port6', vlanid=0, speed='1000auto'),
                            wan=WAN(
                                # inet1=Interface('port1', vlanid=0, speed='1000auto'),
                                # inet2=Interface('port2', vlanid=0, speed='1000auto'),
                                # mpls1=Interface('port4', vlanid=0, speed='1000auto'),
                                inet1=Interface('port1', name="Internet_1", vlanid=71, speed='1000auto'),
                                inet2=Interface('port2', name="Internet_2", vlanid=72, speed='1000auto'),
                                mpls1=Interface('port4', name="MPLS", vlanid=74, speed='1000auto'),
                            ))

SDW_3301E_A = FortiGate(name_fpoc='SDW-3301E-A', alias='SDW-3301E-A', model='FGT_3301E', password='Fortinet123#',
                            npu='NP6', reboot_delay=300,
                            mgmt=Interface('mgmt1', 0, '10.210.0.63/23'),
                            lan=Interface('port6', vlanid=0, speed='auto'),
                            wan=WAN(
                                # inet1=Interface('port1', vlanid=0, speed='auto'),
                                # inet2=Interface('port2', vlanid=0, speed='auto'),
                                # mpls1=Interface('port4', vlanid=0, speed='auto'),
                                inet1=Interface('port1', name="Internet_1", vlanid=71, speed='auto'),
                                inet2=Interface('port2', name="Internet_2", vlanid=72, speed='auto'),
                                mpls1=Interface('port4', name="MPLS", vlanid=74, speed='auto'),
                            ))

SDW_3301E_B = FortiGate(name_fpoc='SDW-3301E-B', alias='SDW-3301E-B', model='FGT_3301E', password='Fortinet123#',
                            npu='NP6', reboot_delay=300,
                            mgmt=Interface('mgmt1', 0, '10.210.0.67/23'),
                            lan=Interface('port6', vlanid=0, speed='auto'),
                            wan=WAN(
                                # inet1=Interface('port1', vlanid=0, speed='auto'),
                                # inet2=Interface('port2', vlanid=0, speed='auto'),
                                # mpls1=Interface('port4', vlanid=0, speed='auto'),
                                inet1=Interface('port1', name="Internet_1", vlanid=71, speed='auto'),
                                inet2=Interface('port2', name="Internet_2", vlanid=72, speed='auto'),
                                mpls1=Interface('port4', name="MPLS", vlanid=74, speed='auto'),
                            ))

SDW_101F_A = FortiGate(name_fpoc='SDW-101F-A', alias='SDW-101F-A', model='FGT_101F', password='Fortinet123#',
                            npu='SoC4', reboot_delay=180,
                            mgmt=Interface('mgmt', 0, '10.210.0.23/23'),
                            lan=Interface('port4', vlanid=0, speed='auto'),
                            wan=WAN(
                                # inet1=Interface('wan1', vlanid=0, speed='auto'),
                                # inet2=Interface('wan2', vlanid=0, speed='auto'),
                                # mpls1=Interface('port2', vlanid=0, speed='auto'),
                                inet1=Interface('wan1', name="Internet_1", vlanid=71, speed='auto'),
                                inet2=Interface('wan2', name="Internet_2", vlanid=72, speed='auto'),
                                mpls1=Interface('port2', name="MPLS", vlanid=74, speed='auto'),
                            ))

SDW_101F_B = FortiGate(name_fpoc='SDW-101F-B', alias='SDW-101F-B', model='FGT_101F', password='Fortinet123#',
                            npu='SoC4', reboot_delay=180,
                            mgmt=Interface('mgmt', 0, '10.210.0.41/23'),
                            lan=Interface('port4', vlanid=0, speed='auto'),
                            wan=WAN(
                                # inet1=Interface('wan1', vlanid=0, speed='auto'),
                                # inet2=Interface('wan2', vlanid=0, speed='auto'),
                                # mpls1=Interface('port2', vlanid=0, speed='auto'),
                                inet1=Interface('wan1', name="Internet_1", vlanid=71, speed='auto'),
                                inet2=Interface('wan2', name="Internet_2", vlanid=72, speed='auto'),
                                mpls1=Interface('port2', name="MPLS", vlanid=74, speed='auto'),
                            ))

SDW_50G_A = FortiGate(name_fpoc='SDW-50G-A', alias='SDW-50G-A', model='FWF_50G', password='Fortinet123#',
                            npu='SoC5', reboot_delay=120,
                            mgmt=Interface('lan2', 0, '10.210.0.250/23'),
                            lan=Interface('lan', vlanid=0, speed=None), # speed None since 'lan' is in a virtual-switch
                            wan=WAN(
                                # inet1=Interface('wan1', vlanid=0, speed='auto'),
                                # inet2=Interface('port1', vlanid=0, speed='auto'),
                                # mpls1=Interface('port2', vlanid=0, speed='auto'),
                                inet1=Interface('wan', name="Internet_1", vlanid=71, speed='auto'),
                                inet2=Interface('wan', name="Internet_2", vlanid=73, speed='auto'),
                                mpls1=Interface('wan', name="MPLS", vlanid=74, speed='auto'),
                            ))

SDW_50G_B = FortiGate(name_fpoc='SDW-50G-B', alias='SDW-50G-B', model='FWF_50G', password='Fortinet123#',
                            npu='SoC5', reboot_delay=120,
                            mgmt=Interface('lan2', 0, '10.210.0.255/23'),
                            lan=Interface('lan', vlanid=0, speed=None), # speed None since 'lan' is in a virtual-switch
                            wan=WAN(
                                # inet1=Interface('wan1', vlanid=0, speed='auto'),
                                # inet2=Interface('port1', vlanid=0, speed='auto'),
                                # mpls1=Interface('port2', vlanid=0, speed='auto'),
                                inet1=Interface('wan', name="Internet_1", vlanid=71, speed='auto'),
                                inet2=Interface('wan', name="Internet_2", vlanid=73, speed='auto'),
                                mpls1=Interface('wan', name="MPLS", vlanid=74, speed='auto'),
                            ))
