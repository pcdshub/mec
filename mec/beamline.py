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

#with safe_load('target xy stage'):
#    from .devices import TargetXYStage
#    from pcdsdevices import epics_motor 
#    target_y = epics_motor.Newport('MEC:PPL:MMN:09', name='target y')
#    tgt = TargetXYStage(target_x, target_y, 3.7, 3.5)

#with safe_load('event sequencer'):
#    from pcdsdevices.sequencer import EventSequencer
#    seq = EventSequencer('ECS:SYS0:6', name='seq_6')

with safe_load('event sequencer'):
    from pcdsdevices.sequencer import EventSequencer
    seq = EventSequencer('ECS:SYS0:6', name='seq_6')
#    seq = EventSequencer('FAKE:ECS:SYS0:6', name='seq_6')

#with safe_load('fake event sequencer'):
#    from pcdsdevices.sequencer import EventSequencer
#    fake_seq = EventSequencer('FAKE:ECS:SYS0:6', name='fake_seq_6')

#with safe_load('event sequence'):
#    from pcdsdevices.sequencer import EventSequence

with safe_load('slits'):
    from pcdsdevices.slits import Slits
    slit1 = Slits('HXX:UM6:JAWS', name='slit1')
    slit2 = Slits('MEC:XT1:JAWS:US', name='slit2')
    slit3 = Slits('MEC:XT1:JAWS:DS', name='slit3')
    slit4 = Slits('MEC:XT2:JAWS', name='slit4')


with safe_load('YAG screens'): # Also known as PIMs
    from pcdsdevices.pim import PIM, PIMY
    mec_yag0 = PIMY('HXX:HXM:PIM', name='mec yag0')
    yag0 = mec_yag0
    mec_yag1 = PIMY('MEC:HXM:PIM', name='mec yag1')
    yag1 = mec_yag1
    mec_yag2 = PIMY('MEC:PIM2', name='mec yag2')
    yag2 = mec_yag2
    mec_yag3 = PIMY('MEC:PIM3', name='mec yag3')
    yag3 = mec_yag3

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
    from .laser_devices import Highland
    nsl_highland = Highland('MEC:LPL:AMD:01', name='mec highland')

with safe_load('SiT'):
    from mec.db import mec_attenuator
    SiT = mec_attenuator
#    from pcdsdevices.attenuator import Attenuator
#    att = Attenuator('IOC:MEC:ATT', 10, name='mec attenuator')


with safe_load('Visar Beds'):
    from .visar_bed import VisarBed
    bed1=VisarBed('MEC:NOTE:VIS:CAM1', name="Visar Bed1")
    bed2=VisarBed('MEC:NOTE:VIS:CAM2', name="Visar Bed2")

with safe_load('long pulse waveplates'):
    from pcdsdevices import epics_motor
    wp_ab = epics_motor.IMS('MEC:NS1:MMS:02', name='waveplate AB')
    wp_ef = epics_motor.IMS('MEC:NS1:MMS:01', name='waveplate EF')
    wp_gh = epics_motor.Newport('MEC:LAS:MMN:30', name='waveplate GH')
    wp_ij = epics_motor.Newport('MEC:LAS:MMN:29', name='waveplate IJ')

with safe_load('testmotors'):
    from pcdsdevices import epics_motor 
    test_1 = epics_motor.Newport('MEC:PPL:MMN:23', name='test 1')
    test_2 = epics_motor.Newport('MEC:PPL:MMN:24', name='test 2')

with safe_load('daq'):
    from pcdsdaq.daq import Daq
    from mec.db import RE
    daq = Daq(RE=RE)
#with safe_load('Nanosecond laser'):
#    from .laser import NanoSecondLaser
#    nsl = NanoSecondLaser()

with safe_load('mec timing'):
    from .mec_timing import FSTiming, NSTiming, lpl_save_master_timing
    fstiming = FSTiming()
    nstiming = NSTiming()

with safe_load('SPL Modes'):
    from .spl_modes import DG645
    from .spl_modes import UniblitzEVRCH

    las_dg = DG645('MEC:LAS:DDG:08', name='uniblitz dg')
    las_evr = UniblitzEVRCH('LAS:MEC:EVR:03:TRIG2', name='uniblitz las evr')
    uni_evr = UniblitzEVRCH('EVR:MEC:USR01:TRIG5', name='uniblitz usr evr')

    wt = 0.5 # sleep time between commands

    def spl_align():
        print("Disabling Slicer...")
        las_evr.ch_enable.put(0) # Disable
        time.sleep(wt)
        print("Disabling Shutters...")
        uni_evr.ch_enable.put(0) # Disable
        time.sleep(wt)
        print("Opening Shutters...")
        las_dg.ch_AB_pol.put(0)  # Negative
        las_dg.ch_CD_pol.put(0)  # Negative
        time.sleep(wt)
        print("Setting laser to 5 Hz...")
        las_evr.ch_eventc.put(44)
        time.sleep(wt)
        print("Laser is in alignment mode.")
        print("Remember to change to target mode after alignment.")

    def spl_target():
        print("Setting laser to single shot...")
        las_evr.ch_eventc.put(176)
        time.sleep(wt)
        print("Disabling Slicer...")
        las_evr.ch_enable.put(0) # Disable
        time.sleep(wt)
        print("Enabling Shutters...")
        uni_evr.ch_enable.put(1) # Enable
        time.sleep(wt)
        print("Closing Shutters...")
        las_dg.ch_AB_pol.put(1)  # Positive
        las_dg.ch_CD_pol.put(1)  # Positive
        time.sleep(wt)
        print("Enabling Slicer...")
        las_evr.ch_enable.put(1) # Enable
        time.sleep(wt)
        print("Setting up Event Sequencer...")
        s = [[177,0,0,0], [176,24,0,0]]
        seq.sequence.put_seq(s)
        print("Laser is in target mode. Single shot only!!!.")
        print("Don't forget to use the --prelasertrig 24 option in the script!!")
        print("Remember to change to alignment mode before aligning.")
