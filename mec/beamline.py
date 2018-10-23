from hutch_python.utils import safe_load
import time


with safe_load('shutters'):
    from .devices import TCShutter
    shutter1 = TCShutter("MEC:USR:DOUT1", name='TC Shutter 1')
    shutter2 = TCShutter("MEC:USR:DOUT2", name='TC Shutter 2')
    shutter3 = TCShutter("MEC:USR:DOUT3", name='TC Shutter 3')
    shutter4 = TCShutter("MEC:USR:DOUT4", name='TC Shutter 4')
    shutter5 = TCShutter("MEC:USR:DOUT5", name='TC Shutter 5')
    shutter6 = TCShutter("MEC:USR:DOUT6", name='TC Shutter 6')


with safe_load('chamber lights'):
    from .devices import LedLights
    focusedchamberlight = LedLights("MEC:PR60:PWR:1:Outlet:1", name='focused chamber light')
    brightchamberlight = LedLights("MEC:PR60:PWR:1:Outlet:6", name='bright chamber light')
    #visarlight = LedLights("MEC:PR60:PWR:1:Outlet:8", name='visar light') # Not currently plugged in
    def lights_on():
        focusedchamberlight.on()
        brightchamberlight.on()
        #visarlight.on()
    def lights_off():
        focusedchamberlight.off()
        brightchamberlight.off()
        #visarlight.off()


with safe_load('target x'):
    from pcdsdevices import epics_motor 
    target_x = epics_motor.IMS('MEC:USR:MMS:17', name='target x')


with safe_load('target hexapod'):
    from .devices import PI_M824_Hexapod 
    tc_hexapod = PI_M824_Hexapod('MEC:HEX:01', name='target hexapod') 

    from .devices import TargetStage
    target = TargetStage(target_x, tc_hexapod, 0.75, 0.75)


with safe_load('event sequencer'):
    from pcdsdevices.sequencer import EventSequencer
    seq = EventSequencer('ECS:SYS0:6', name='seq_6')

#with safe_load('event sequence'):
#    from pcdsdevices.sequencer import EventSequence

with safe_load('slits'):
    from pcdsdevices.slits import Slits
    slit1 = Slits('HXX:UM6:JAWS', name='slit1')
    slit2 = Slits('MEC:XT1:JAWS:US', name='slit2')
    slit3 = Slits('MEC:XT1:JAWS:DS', name='slit3')
    slit4 = Slits('MEC:XT2:JAWS', name='slit4')


with safe_load('YAG screens'): # Also known as PIMs
    from pcdsdevices.pim import PIM
    from pcdsdevices.pim import PIMMotor
    #mec_yag0 = mec_pim1
    mec_yag0 = PIM('HXX:UM6:MMS:08', prefix_det='HXX:UM6:CVV:01', name='mec yag0')# ==works
    mec_yag1 = PIM('MEC:HXM:MMS:16', prefix_det='MEC:HXM:CVV:01', name='mec yag1')# ==works
    mec_yag2 = PIMMotor('MEC:XT2:MMS:13', name='mec yag2')
    #mec_yag2 = PIM('MEC:XT2:MMS:13', prefix_det='MEC:XT2:CVV:01', name='mec yag2')# !=works
    mec_yag3 = PIMMotor('MEC:XT2:MMS:29', name='mec yag3')
    #mec_yag3 = PIM('MEC:XT2:MMS:29', prefix_det='MEC:XT2:CVV:02', name='mec yag3')# !=works
    def yags_out():
        mec_yag0.remove()
        time.sleep(0.1)
        mec_yag1.remove()
        time.sleep(0.1)
        mec_yag2.remove()
        time.sleep(0.1)
        mec_yag3.remove()

    def yags_in():
        mec_yag0.insert()
        time.sleep(0.1)
        mec_yag1.insert()
        time.sleep(0.1)
        mec_yag2.insert()
        time.sleep(0.1)
        mec_yag3.insert()

        
with safe_load('IPMs'):
    from pcdsdevices.ipm import IPM
    mec_ipm1 = IPM('MEC:HXM:IPM:01', name='mec ipm1')
    mec_ipm2 = IPM('MEC:XT2:IPM:02', name='mec ipm2')
    mec_ipm3 = IPM('MEC:XT2:IPM:03', name='mec ipm3')

with safe_load('Highland'):
    from .laser import Highland
    nsl_highland = Highland('MEC:LPL:AMD:01', name='mec highland')

