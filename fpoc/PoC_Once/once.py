from fpoc.PoC_SDWAN import FabricStudioSDWAN, AgoraSDWAN

######### CURRENT POC = POC01  #############################
from .once01 import devices
############################################################

class FabricStudioPoCOnce(FabricStudioSDWAN):
    """
    """
    template_folder = 'PoC_Once'
    devices = devices
