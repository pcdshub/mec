# Module for setting up the MEC "slow cameras" (PI-MTE, Pixis, etc.)

#import pycdb.Db
import os
import pycdb
from mec.db import daq#, seq
import pydaq
import logging
from mec.sequence import Sequence

logger = logging.getLogger(__name__)

class SlowCameras():
    """Helper class for configuring the MEC slow cameras."""

    def __init__(self):
        self.alias = "LASER_SIM"
        self._seq = Sequence()
        self._cdb = pycdb.Db(daq._control.dbpath())

    def stage(self, laser_config):
        # Set exposure delay using laser config
        ExposureTime = laser_config['slowcamdelay'] 
        newkey = self._cdb.get_key(self.alias)
        print("Before partition")    
        partition = daq._control.partition()
        print("After partition")    

        lAllocatedPrinceton = []
        lAllocatedFli       = []
        lAllocatedAndor     = []
        lAllocatedPimax     = []
        lAllocatedPixis     = []

        for daqNode in partition['nodes']:
            # example of daqNode: {'record': True, 'phy': 256L, 'id': 'NoDetector-0|Evr-0', 'readout': True}
            phy = daqNode['phy']
            devId = ((phy & 0x0000FF00) >> 8)
            devNo = (phy & 0x000000FF)
            if devId == 6: # Princeton
                lAllocatedPrinceton.append((phy,devNo))
            elif devId == 23:
                lAllocatedFli.append((phy,devNo))
            elif devId == 25:
                lAllocatedAndor.append((phy,devNo))
            elif devId == 32:
                lAllocatedPimax.append((phy,devNo))
            elif devId == 46:
                lAllocatedPixis.append((phy,devNo))

        for (phy,iCamera) in lAllocatedPrinceton:
            print("Before lXtc")
            lXtcPrinceton = self._cdb.get(key=newkey,src=phy)
            print("Princeton %d (detector id: 0x%x)" % (iCamera, phy))
            if len(lXtcPrinceton) != 1:
                print("!! Error: Princeton %d should only have one config, but found %d configs" % (iCamera, len(lXtcPrinceton)))
                continue
            xtc              = lXtcPrinceton[0]
            configPrinceton  = xtc.get()
            fOrgExposureTime = float(configPrinceton['exposureTime'])
            width            = configPrinceton['width']
            height           = configPrinceton['height']
            speed            = configPrinceton['readoutSpeedIndex']
            kineticHeight    = configPrinceton['kineticHeight']
    
            configPrinceton['exposureEventCode'] = self._seq.EC['slowcam']
    
            print("  W %d H %d speed %d code %d" % (width, height, speed, configPrinceton['exposureEventCode']))
    
            if kineticHeight == 0:
                print("  Exposure time (Original) [%d]: %.3f s" % (iCamera, fOrgExposureTime))
                configPrinceton['exposureTime']     = ExposureTime
                print("  Exposure time (New)      [%d]: %.3f s" % (iCamera, configPrinceton['exposureTime']))
            else:
                print("  !!! Kinetics mode is not supported in this script")
                return 1
    
            configPrinceton['numDelayShots'] = laser_config['during']
            print("  Number of Delayed Shots: [%d]: %d" % (iCamera, configPrinceton['numDelayShots']))
    
            xtc.set(configPrinceton)
            self._cdb.set(xtc = xtc, alias = self.alias)
    
        for (phy,iCamera) in lAllocatedAndor:
            lXtcAndor = self._cdb.get(key=newkey,src=phy)
            print("Andor %d (detector id: 0x%x)" % (iCamera, phy))
            if len(lXtcAndor) != 1:
              print("!! Error: Andor %d should only have one config, but found %d configs" % (iCamera, len(lXtcAndor)))
              continue
            xtc              = lXtcAndor[0]
            configAndor      = xtc.get()
            fOrgExposureTime = float(configAndor['exposureTime'])
            width            = configAndor['width']
            height           = configAndor['height']
            speed            = configAndor['readoutSpeedIndex']
           
            configAndor['exposureEventCode'] = self._seq.EC['slowcam']
            print("  W %d H %d speed %d code %d" % (width, height, speed, configAndor['exposureEventCode']))
            
            print("  Exposure time (Original) [%d]: %.3f s" % (iCamera, fOrgExposureTime))
            configAndor['exposureTime']     = ExposureTime
            print("  Exposure time (New)      [%d]: %.3f s" % (iCamera, ExposureTime))
            configAndor['numDelayShots'] = laser_config['during']
            print("  Number of Delayed Shots: [%d]: %d" % (iCamera, configAndor['numDelayShots']))
           
            xtc.set(configAndor)
            self._cdb.set(xtc = xtc, alias = self.alias)

        for (phy,iCamera) in lAllocatedPimax:
            lXtcPimax = self._cdb.get(key=newkey,src=phy)
            print("Pimax %d (detector id: 0x%x)" % (iCamera, phy))
            if len(lXtcPimax) != 1:
              print("!! Error: Pimax %d should only have one config, but found %d configs" % (iCamera, len(lXtcPimax)))
              continue
            xtc              = lXtcPimax[0]
            configPimax      = xtc.get()
            fOrgExposureTime = float(configPimax['exposureTime'])
            width            = configPimax['width']
            height           = configPimax['height']
            speed            = configPimax['readoutSpeed']
            code             = configPimax['exposureEventCode']
            
            configPimax['exposureEventCode'] = self._seq.EC['slowcam']
            
            fReadoutTime = 1 / speed
            
            print("  W %d H %d speed %d code %d readout %.3f" % (width, height, speed, configPimax['exposureEventCode'], fReadoutTime))
            print("  Exposure time (Original) [%d]: %.3f s" % (iCamera, fOrgExposureTime))
            configPimax['exposureTime']     = ExposureTime
            print("  Exposure time (New)      [%d]: %.3f s" % (iCamera, configPimax['exposureTime']))
            
            configPimax['numIntegrationShots'] = laser_config['during']
            print("  Number of Integration Shots: [%d]: %d" % (iCamera, configPimax['numIntegrationShots']))
            
            xtc.set(configPimax)
            self._cdb.set(xtc = xtc, alias = self.alias)

        for (phy,iCamera) in lAllocatedPixis:
            lXtcPixis = self._cdb.get(key=newkey,src=phy)
            print("Pixis %d (detector id: 0x%x)" % (iCamera, phy))
            if len(lXtcPixis) != 1:
                print("!! Error: Pixis %d should only have one config, but found %d configs" % (iCamera, len(lXtcPixis)))
                continue
            xtc              = lXtcPixis[0]
            configPixis      = xtc.get()
            fOrgExposureTime = float(configPixis['exposureTime'])
            width            = configPixis['width']
            height           = configPixis['height']
            speed            = configPixis['readoutSpeed']
            code             = configPixis['exposureEventCode']
    
            configPixis['exposureEventCode'] = self._seq.EC['slowcam']
    
            fReadoutTime = 1 / speed
    
            print("  W %d H %d speed %d code %d readout %.3f" % (width, height, speed, configPixis['exposureEventCode'], fReadoutTime))
            print("  Exposure time (Original) [%d]: %.3f s" % (iCamera, fOrgExposureTime))
            configPixis['exposureTime']     = ExposureTime
            print("  Exposure time (New)      [%d]: %.3f s" % (iCamera, configPixis['exposureTime']))
    
            configPixis['numIntegrationShots'] = laser_config['during']
            print("  Number of Integration Shots: [%d]: %d" % (iCamera, configPixis['numIntegrationShots']))
    
            xtc.set(configPixis)
            self._cdb.set(xtc = xtc, alias = self.alias)
    
        self._cdb.commit()
                    
    def unstage(self):
        """Unstage the slow cameras."""
        # Added for completeness and future changes. Nothing really to do,
        # so just pass.
        pass
