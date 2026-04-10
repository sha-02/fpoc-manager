from fpoc.PoC_SDWAN import FabricStudioSDWAN

# List of devices that is imported by once.py to build the class
devices = {
    'HUB': FabricStudioSDWAN.devices['WEST-DC1'],
    'BRANCH1': FabricStudioSDWAN.devices['WEST-BR1'],
    'BRANCH2': FabricStudioSDWAN.devices['WEST-BR2'],
}
