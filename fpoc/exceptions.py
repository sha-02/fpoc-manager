class FpocManagerException(Exception):
    """ Base Exception class for this project """


class CompletedDeviceProcessing(FpocManagerException):
    """ Exception used when processing of a Device completed successfully """


class StopProcessingDevice(FpocManagerException):
    """ Exception used to stop processing of current Device when there was an issue for the Device """


class ReProcessDevice(FpocManagerException):
    """ Exception used to process once again the same Device """
    def __init__(self, *args, sleep=0):
        self.sleep = sleep
        super(ReProcessDevice, self).__init__(*args)    # propagate the exception


class AbortDeployment(FpocManagerException):
    """ Exception used to abort deployment """
