from fpoc.PoC_SDWAN import FabricStudioSDWAN, AtriumSDWAN

######### CURRENT POC = POC02  #############################
from .once02 import devices_fabric_studio, devices_atrium
# EXECUTION_ENVIRONMENT = "FabricStudio"
EXECUTION_ENVIRONMENT = "Atrium"
############################################################

class FabricStudioPoCOnce(FabricStudioSDWAN):
    """
    """
    template_folder = 'PoC_Once'
    devices = devices_fabric_studio


class AtriumPoCOnce(AtriumSDWAN):
    """
    """
    template_folder = 'PoC_Once'
    devices = impairment = no_impairment = devices_atrium