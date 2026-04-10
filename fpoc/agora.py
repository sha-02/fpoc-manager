from fpoc import FortiGate, WAN, Interface

# Define each FGT appliance in Agora Hardware Lab

SDW_agora = dict()


### 1001F-A, 1001F-B

FGT_1001F = FortiGate(model='FGT_1001F', npu='NP7', reboot_delay=300)
FGT_A = FortiGate(name_phy='SDW-1001F-A', alias='SDW-1001F-A', password='Fortinet123#',
                  mgmt=Interface('mgmt', 0, '10.210.0.59/23'),
                  lan=Interface('port6', vlanid=0, speed='1000auto'),
                  )
FGT_B = FortiGate(name_phy='SDW-1001F-B', alias='SDW-1001F-B', password='Fortinet123#',
                  mgmt=Interface('mgmt', 0, '10.210.0.50/23'),
                  lan=Interface('port6', vlanid=0, speed='1000auto'),
                  )
wan_impairment = FortiGate(wan=WAN(
    inet1=Interface('port1', vlanid=0, speed='1000auto'),
    inet2=Interface('port2', vlanid=0, speed='1000auto'),
    mpls1=Interface('port4', vlanid=0, speed='1000auto'),
    ))
wan_no_impairment = FortiGate(wan=WAN(
    inet1=Interface('port1', name="Internet_1", vlanid=71, speed='1000auto'),
    inet2=Interface('port2', name="Internet_2", vlanid=72, speed='1000auto'),
    mpls1=Interface('port4', name="MPLS", vlanid=74, speed='1000auto'),
    ))

SDW_agora['SDW_1001F_A'] = {
    'impairment': FGT_1001F.update(FGT_A).update(wan_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.11.1/24'),
                                inet2=Interface(address='100.64.12.1/24'),
                                mpls1=Interface(address='10.71.14.1/24'),
                            ))),
    'no-impairment': FGT_1001F.update(FGT_A).update(wan_no_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.71.1/24'),
                                inet2=Interface(address='100.64.72.1/24'),
                                mpls1=Interface(address='10.71.74.1/24'),
                            ))),
    }

SDW_agora['SDW_1001F_B'] = {
    'impairment': FGT_1001F.update(FGT_B).update(wan_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.21.1/24'),
                                inet2=Interface(address='100.64.22.1/24'),
                                mpls1=Interface(address='10.71.24.1/24'),
                            ))),
    'no-impairment': FGT_1001F.update(FGT_B).update(wan_no_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.71.2/24'),
                                inet2=Interface(address='100.64.72.2/24'),
                                mpls1=Interface(address='10.71.74.2/24'),
                            ))),
    }


### 3301E-A, 3301E-B

FGT_3301E = FortiGate(model='FGT_3301E', npu='NP7', reboot_delay=300)
FGT_A = FortiGate(name_phy='SDW-3301E-A', alias='SDW-3301E-A', password='Fortinet123#',
                  mgmt=Interface('mgmt1', 0, '10.210.0.63/23'),
                  lan=Interface('port6', vlanid=0, speed='auto'),
                  )
FGT_B = FortiGate(name_phy='SDW-3301E-B', alias='SDW-3301E-B', password='Fortinet123#',
                  mgmt=Interface('mgmt1', 0, '10.210.0.67/23'),
                  lan=Interface('port6', vlanid=0, speed='auto'),
                  )
wan_impairment = FortiGate(wan=WAN(
    inet1=Interface('port1', vlanid=0, speed='1000auto'),
    inet2=Interface('port2', vlanid=0, speed='1000auto'),
    mpls1=Interface('port4', vlanid=0, speed='1000auto'),
    ))
wan_no_impairment = FortiGate(wan=WAN(
    inet1=Interface('port1', name="Internet_1", vlanid=71, speed='1000auto'),
    inet2=Interface('port2', name="Internet_2", vlanid=72, speed='1000auto'),
    mpls1=Interface('port4', name="MPLS", vlanid=74, speed='1000auto'),
    ))

SDW_agora['SDW_3301E_A'] = {
    'impairment': FGT_3301E.update(FGT_A).update(wan_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.51.1/24'),
                                inet2=Interface(address='100.64.52.1/24'),
                                mpls1=Interface(address='10.71.54.1/24'),
                            ))),
    'no-impairment': FGT_3301E.update(FGT_A).update(wan_no_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.71.5/24'),
                                inet2=Interface(address='100.64.72.5/24'),
                                mpls1=Interface(address='10.71.74.5/24'),
                            ))),
    }

SDW_agora['SDW_3301E_B'] = {
    'impairment': FGT_3301E.update(FGT_B).update(wan_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.61.1/24'),
                                inet2=Interface(address='100.64.62.1/24'),
                                mpls1=Interface(address='10.71.64.1/24'),
                            ))),
    'no-impairment': FGT_3301E.update(FGT_B).update(wan_no_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.71.6/24'),
                                inet2=Interface(address='100.64.72.6/24'),
                                mpls1=Interface(address='10.71.74.6/24'),
                            ))),
    }


## 101F-A, 101F-B

FGT_101F = FortiGate(model='FGT_101F', npu='SoC4', reboot_delay=180 )
FGT_A = FortiGate(name_phy='SDW-101F-A', alias='SDW-101F-A', password='Fortinet123#',
                  mgmt=Interface('mgmt', 0, '10.210.0.23/23'),
                  lan=Interface('port4', vlanid=0, speed='auto'),
                  )
FGT_B = FortiGate(name_phy='SDW-101F-B', alias='SDW-101F-B', password='Fortinet123#',
                  mgmt=Interface('mgmt', 0, '10.210.0.41/23'),
                  lan=Interface('port4', vlanid=0, speed='auto'),
                  )
wan_impairment = FortiGate(wan=WAN(
    inet1=Interface('wan1', vlanid=0, speed='auto'),
    inet2=Interface('wan2', vlanid=0, speed='auto'),
    mpls1=Interface('port2', vlanid=0, speed='auto'),
    ))
wan_no_impairment = FortiGate(wan=WAN(
    inet1=Interface('wan1', name="Internet_1", vlanid=71, speed='auto'),
    inet2=Interface('wan2', name="Internet_2", vlanid=72, speed='auto'),
    mpls1=Interface('port2', name="MPLS", vlanid=74, speed='auto'),
    ))


SDW_agora['SDW_101F_A'] = {
    'impairment': FGT_101F.update(FGT_A).update(wan_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.31.1/24'),
                                inet2=Interface(address='100.64.32.1/24'),
                                mpls1=Interface(address='10.71.34.1/24'),
                            ))),
    'no-impairment': FGT_101F.update(FGT_A).update(wan_no_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.71.3/24'),
                                inet2=Interface(address='100.64.72.3/24'),
                                mpls1=Interface(address='10.71.74.3/24'),
                            ))),
    }

SDW_agora['SDW_101F_B'] = {
    'impairment': FGT_101F.update(FGT_B).update(wan_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.41.1/24'),
                                inet2=Interface(address='100.64.42.1/24'),
                                mpls1=Interface(address='10.71.44.1/24'),
                            ))),
    'no-impairment': FGT_101F.update(FGT_B).update(wan_no_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.71.4/24'),
                                inet2=Interface(address='100.64.72.4/24'),
                                mpls1=Interface(address='10.71.74.4/24'),
                            ))),
    }


## 50G-A, 50G-B

FGT_50G = FortiGate(model='FWF_50G', npu='SoC5', reboot_delay=120 )
FGT_A = FortiGate(name_phy='SDW-50G-A', alias='SDW-50G-A', password='Fortinet123#',
                  mgmt=Interface('lan2', 0, '10.210.0.250/23'),
                  lan=Interface('lan', vlanid=0, speed=None),  # speed None since 'lan' is in a virtual-switch
                  )
FGT_B = FortiGate(name_phy='SDW-50G-B', alias='SDW-50G-B', password='Fortinet123#',
                  mgmt=Interface('lan2', 0, '10.210.0.255/23'),
                  lan=Interface('lan', vlanid=0, speed=None),  # speed None since 'lan' is in a virtual-switch
                  )
wan_impairment = FortiGate(wan=WAN(
    inet1=Interface('wan1', vlanid=0, speed='auto'),
    inet2=Interface('port1', vlanid=0, speed='auto'),
    mpls1=Interface('port2', vlanid=0, speed='auto'),
    ))
wan_no_impairment = FortiGate(wan=WAN(
    inet1=Interface('wan', name="Internet_1", vlanid=71, speed='auto'),
    inet2=Interface('wan', name="Internet_2", vlanid=73, speed='auto'),
    mpls1=Interface('wan', name="MPLS", vlanid=74, speed='auto'),
    ))

SDW_agora['SDW_50G_A'] = {
    'impairment': FGT_50G.update(FGT_A).update(wan_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.91.1/24'),
                                inet2=Interface(address='100.64.92.1/24'),
                                mpls1=Interface(address='10.71.94.1/24'),
                            ))),
    'no-impairment': FGT_50G.update(FGT_A).update(wan_no_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.71.9/24'),
                                inet2=Interface(address='100.64.72.9/24'),
                                mpls1=Interface(address='10.71.74.9/24'),
                            ))),
    }

SDW_agora['SDW_50G_B'] = {
    'impairment': FGT_50G.update(FGT_B).update(wan_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.101.1/24'),
                                inet2=Interface(address='100.64.102.1/24'),
                                mpls1=Interface(address='10.71.104.1/24'),
                            ))),
    'no-impairment': FGT_50G.update(FGT_B).update(wan_no_impairment).update(FortiGate(wan=WAN(
                                inet1=Interface(address='100.64.71.10/24'),
                                inet2=Interface(address='100.64.72.10/24'),
                                mpls1=Interface(address='10.71.74.10/24'),
                            ))),
    }

