from fpoc.PoC_SDWAN import FabricStudioSDWAN, AgoraSDWAN

######### CURRENT POC = POC02  #############################
from .once02 import devices
############################################################

class FabricStudioPoCOnce(FabricStudioSDWAN):
    """
    """
    template_folder = 'PoC_Once'
    devices = devices
