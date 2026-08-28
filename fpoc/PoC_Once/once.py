from fpoc.PoC_SDWAN import FabricStudioSDWAN, AgoraSDWAN

######### CURRENT POC = POC02  #############################
from .once02 import devices_fabric_studio, devices_agora
# EXECUTION_ENVIRONMENT = "FabricStudio"
EXECUTION_ENVIRONMENT = "Agora"
############################################################

class FabricStudioPoCOnce(FabricStudioSDWAN):
    """
    """
    template_folder = 'PoC_Once'
    devices = devices_fabric_studio


class AgoraPoCOnce(AgoraSDWAN):
    """
    """
    template_folder = 'PoC_Once'
    devices = impairment = no_impairment = devices_agora