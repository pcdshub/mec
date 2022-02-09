import time
import numpy as np
from datetime import datetime
#from mec.laser import NanoSecondLaser
#import logging

#import elog
#import pickle
from mecps import *

from pcdsdevices.epics_motor import Motor

from mec.db import *
from mec.beamline import *
from mec.devices import *
from mec.laser import *
from mec.laser_devices import *
from mec.spl_modes import *
from mec.sequence import *
from mec.slowcams import *
from mec.visar_bed import *

# using a function from Tyler's timing module for the VISAR streaks
#from mec.mec_timing import TimingChannel

from ophyd import EpicsSignal 

#logger = logging.getLogger(__name__)

#thz_motor = Motor('MEC:USR:MMS:17', name='thz_motor')
#spl_motor = Motor('MEC:USR:MMS:17', name='spl_motor')
ref_y = Motor('MEC:XT1:MMS:01', name='ref_y')
tgx=Motor('MEC:USR:MMS:17', name='tgx')
hexx=EpicsSignal('MEC:HEX:01:Xpr')
hexy=EpicsSignal('MEC:HEX:01:Ypr')
hexz=EpicsSignal('MEC:HEX:01:Zpr')
s500mm=EpicsSignal('MEC:PPL:MMN:13')
tgy=EpicsSignal('MEC:PPL:MMN:07')
tgy_rbv=EpicsSignal('MEC:PPL:MMN:07.RBV')
tgz=EpicsSignal('MEC:PPL:MMN:08')
tgz_rbv=EpicsSignal('MEC:PPL:MMN:08.RBV')

delay_line=Motor('MEC:USR:MMS:25', name='delay_line')
pp=EpicsSignal('MEC:HXM:MMS:18:SET_SE')
be_lens_stack=EpicsSignal("MEC:XT2:XFLS.VAL")

# spl timing
spl_vitara = EpicsSignal('LAS:FS6:VIT:FS_TGT_TIME')
spl_vitara_pv = EpicsSignal('MEC:NOTE:LAS:FST0')

# laser uniblitz
spl_uniblitz_evr_code = EpicsSignal('EVR:MEC:USR01:TRIG5:TEC')
spl_uniblitz_evr_btn = EpicsSignal('EVR:MEC:USR01:TRIG5:TCTL')
# 0: negative
# 1: positive
spl_uniblitz_6mm = EpicsSignal('MEC:LAS:DDG:08:cdOutputPolarityBO')
spl_uniblitz_65mm = EpicsSignal('MEC:LAS:DDG:08:abOutputPolarityBO')
# 2: AB
# 3: AB, CD
spl_uniblitz_inh = EpicsSignal('MEC:LAS:DDG:08:triggerInhibitMO')

### All the user pvs we need for the macro's below:
pinhx=EpicsSignal('MEC:NOTE:DOUBLE:01')
pinhy=EpicsSignal('MEC:NOTE:DOUBLE:02')
pinhz=EpicsSignal('MEC:NOTE:DOUBLE:03')
pintgx=EpicsSignal('MEC:NOTE:DOUBLE:04')

yaghx=EpicsSignal('MEC:NOTE:DOUBLE:05')
yaghy=EpicsSignal('MEC:NOTE:DOUBLE:06')
yaghz=EpicsSignal('MEC:NOTE:DOUBLE:07')
yagtgx=EpicsSignal('MEC:NOTE:DOUBLE:08')

tihx=EpicsSignal('MEC:NOTE:DOUBLE:09')
tihy=EpicsSignal('MEC:NOTE:DOUBLE:10')
tihz=EpicsSignal('MEC:NOTE:DOUBLE:11')
titgx=EpicsSignal('MEC:NOTE:DOUBLE:12')

gridhx=EpicsSignal('MEC:NOTE:DOUBLE:13')
gridhy=EpicsSignal('MEC:NOTE:DOUBLE:14')
gridhz=EpicsSignal('MEC:NOTE:DOUBLE:15')
gridtgx=EpicsSignal('MEC:NOTE:DOUBLE:16')

diode500mm=EpicsSignal('MEC:NOTE:DOUBLE:21')
gige4500mm=EpicsSignal('MEC:NOTE:DOUBLE:22')
neo500mm=EpicsSignal('MEC:NOTE:DOUBLE:23')
spectro500mm=EpicsSignal('MEC:NOTE:DOUBLE:59')

pinholehx=EpicsSignal('MEC:NOTE:DOUBLE:24')
pinholehy=EpicsSignal('MEC:NOTE:DOUBLE:25')
pinholehz=EpicsSignal('MEC:NOTE:DOUBLE:26')
pinholetgx=EpicsSignal('MEC:NOTE:DOUBLE:27')

ceo2hx=EpicsSignal('MEC:NOTE:DOUBLE:28')
ceo2hy=EpicsSignal('MEC:NOTE:DOUBLE:29')
ceo2hz=EpicsSignal('MEC:NOTE:DOUBLE:30')
ceo2tgx=EpicsSignal('MEC:NOTE:DOUBLE:31')

lab6hx=EpicsSignal('MEC:NOTE:DOUBLE:32')
lab6hy=EpicsSignal('MEC:NOTE:DOUBLE:33')
lab6hz=EpicsSignal('MEC:NOTE:DOUBLE:34')
lab6tgx=EpicsSignal('MEC:NOTE:DOUBLE:35')

cuhx=EpicsSignal('MEC:NOTE:DOUBLE:17')
cuhy=EpicsSignal('MEC:NOTE:DOUBLE:18')
cuhz=EpicsSignal('MEC:NOTE:DOUBLE:19')
cutgx=EpicsSignal('MEC:NOTE:DOUBLE:20')

zntgx=EpicsSignal('MEC:NOTE:DOUBLE:53')
znhx=EpicsSignal('MEC:NOTE:DOUBLE:54')
znhy=EpicsSignal('MEC:NOTE:DOUBLE:55')
znhz=EpicsSignal('MEC:NOTE:DOUBLE:56')

targetsavehx=EpicsSignal('MEC:NOTE:DOUBLE:37')
targetsavehy=EpicsSignal('MEC:NOTE:DOUBLE:38')
targetsavehz=EpicsSignal('MEC:NOTE:DOUBLE:39')
targetsavetgx=EpicsSignal('MEC:NOTE:DOUBLE:40')

# getting EVR button status for the SPL slicer
spl_slicer_evr_code = EpicsSignal('LAS:MEC:EVR:03:TRIG2:TEC')
spl_slicer_evr_btn = EpicsSignal('LAS:MEC:EVR:03:TRIG2:TCTL')

# getting EVR button status for the LPL slicer and lamps 
lpl_slicer_evr_btn = EpicsSignal('EVR:MEC:USR01:TRIG7:TCTL')
lpl_lamps_evr_btn = EpicsSignal('EVR:MEC:USR01:TRIG6:TCTL')

# getting charging status from the PFN GUI
lpl_charge_status=EpicsSignal('MEC:PFN:CHARGE_OK') 
lpl_charge_btn=EpicsSignal('MEC:PFN:START_CHARGE') 

# getting event code and EVR button status for the VISAR laser and streak cameras
visar_streak_evt_code = EpicsSignal('EVR:MEC:USR01:TRIG4:TEC')
visar_streak_evr_btn = EpicsSignal('EVR:MEC:USR01:TRIG4:TCTL')
visar_laser_evt_code = EpicsSignal('EVR:MEC:USR01:TRIGA:TEC')
visar_laser_evr_btn = EpicsSignal('EVR:MEC:USR01:TRIGA:TCTL')

def visar1_remote():
    '''
    Description: start a remote session of the VISAR1 PC GUI.
    '''
    os.system('vncviewer 172.21.46.71 &')
    print('Password is:')
    print('Mechutch')

def visar2_remote():
    '''
    Description: start a remote session of the VISAR2 PC GUI.
    '''
    os.system('vncviewer 172.21.46.88 &')
    print('Password is:')
    print('Mechutch')

def scope_timing_remote():
    '''
    Description: start a remote session of the Scope Timing PC GUI.
    '''
    os.system('vncviewer 172.21.46.60 &')

def load_presets():
    '''
    Description: load the presets defined in the file stage_presets.txt located at the path /reg/g/pcds/pyps/apps/hutch-python/mec/mec/macros/. You need to login with your own unix account to modify 3this file.
    '''
    arr_presets = np.loadtxt('/reg/g/pcds/pyps/apps/hutch-python/mec/mec/macros/stage_presets.txt')
    return arr_presets

# method to prepare for visar alignment
def visar_mode(status = 'ready'):
    '''
    Description: get the VISAR triggering system ready for alignment or shot, changing the visar laser and streak camera EVR. It will force the evr button to be enabled.
    IN:
        status: 'ready' for laser shot (182), 'align' for alignment mode (43 and 44), 'daq' for 169 used to control the VISAR in the daq, so used for both alignment and on-shot
    OUT:
        set the EVR to the right value
    '''
    # look at the event code
    if (status == 'ready'):
        visar_streak_evt_code.put(182)
        visar_laser_evt_code.put(182)
    if (status == 'align'):
        visar_streak_evt_code.put(44)
        visar_laser_evt_code.put(43)
    if (status == 'daq'):
        visar_streak_evt_code.put(169)
        visar_laser_evt_code.put(43)
    # look at the button status (enabled:1 or diabled:0)
    if (visar_streak_evr_btn.get() == 0):
        visar_streak_evr_btn.put(1)
    if (visar_laser_evr_btn.get() == 0):
        visar_laser_evr_btn.put(1)

# set the calibrant list used on the MEC calibration cartridge
calibrant_list = ['CeO2', 'ceo2', 'LaB6', 'lab6', 'Ti', 'ti', 'Cu', 'cu', 'Zn', 'zn']

# method to save multiple xray only shotsi and/or visar references
def ref_only(xray_trans=1, xray_num=10, shutters=False, dark=False, daq_end=True, calibrant='', rate=1, visar=False, save=False):
    '''
    Description: script to take xray only events and/or VISAR references.
    IN:
        xray_trans : decimal value of the xray transmission
        xray_num   : number of x-rays to send on target
        dark       : default is False, we do not record a dark run before the reference
        shutters   : default is False, we do not need to close the shutters for references
        calibrant  : if not empty, will move to specified calibrant and take calibration run only
        visar      : True if you want to take visar references
        daq_end    : close the run at the end of a shot. Set to True allows a user to see the result of the shot for longer.
        rate       : rate used to take the reference, it is set to 1 by default bu is changed depending on the options (visar, calib)
        save       : True to save to the DAQ, False otherwise
    OUT:
        execute the plan
    '''
    x.nsl._config['rate']=rate
    # make sure the daq is not connected before starting the command
    if (daq.connected == True):
        daq.disconnect()
    msg = '{} x-ray only shots at {:.4f}% {}.'.format(xray_num, 100.0 * xray_trans, msg_log_target)
    tags_ref = ['reference', 'xray']
    # look at the button status to make sure the VISAR triggers are disabled by default (behind overwritten later with visar option), (enabled:1 or disabled:0)
    if (visar_streak_evr_btn.get() == 1):
        visar_streak_evr_btn.put(0)
    if (visar_laser_evr_btn.get() == 1):
        visar_laser_evr_btn.put(0)

    # force VISAR to false to make sure triggers are not enabled if rate is greater than 1 Hz
    # it also means it changes the rate of acquisition to 1Hz to match VISAR capabilities only when it is set to 1
    if (rate > 1):
        visar = False
        print('Rate is not 1 Hz, so the VISAR is disabled. You should also remove the VISAR from the DAQ partition to prevent damaged events.')

    # check if there is a calibrant in the corresponding argument, needs to be done before visar test
    if (calibrant in calibrant_list):
        print('Running X-ray Calibration shots only.')
        tags_ref = ['calibration', 'xray', calibrant]
        x.nsl._config['rate']=rate
        # start by moving on target
        if ((calibrant == 'CeO2') or (calibrant == 'ceo2')):
            ceo2()
            msg_calib_target = 'on CeO2'
        if ((calibrant == 'LaB6') or (calibrant == 'lab6')):
            lab6()
            msg_calib_target = 'on LaB6'
        if ((calibrant == 'Ti') or (calibrant == 'ti')):
            ti()
            msg_calib_target = 'on Ti'
        if ((calibrant == 'Cu') or (calibrant == 'cu')):
            cu()
            msg_calib_target = 'on Cu 5 mic'
        if ((calibrant == 'Zn') or (calibrant == 'zn')):
            zn()
            msg_calib_target = 'on Zn 2.5 mic'
        # use 10Hz rep rate to get calibration shots only when visar is not triggered
        # use 1Hz rep rate to get calibration shots and move in between shots manually
        if (rate == 1):
            print('You can move between shots (rate = 1 Hz).')
        msg = '{} x-ray only calibration shots at {:.4f}% {}.'.format(xray_num, 100.0 * xray_trans, msg_calib_target)

    if (visar == True):
        # make sure the visar event codes are properly set
        visar_mode(status='daq')
        print('Visar reference is being saved in the DAQ.')
        tags_ref = tags_ref + ['visar']
        msg = '{} x-ray only shots at {:.4f}% and {} visar reference image(s) {}.'.format(xray_num, 100.0 * xray_trans, xray_num, msg_log_target)
        if (calibrant in calibrant_list):
            msg = '{} x-ray only, calibration shots at {:.4f}% and {} visar reference image(s) {}.'.format(xray_num, 100.0 * xray_trans, xray_num, msg_calib_target)

    # check if a dark is necessary
    if (dark == True):
         x.nsl.predark=1
         print('Taking a dark reference image.')
    else:
         x.nsl.predark=0
         print('No dark reference image taken.')
        
    # check if shutters are necessary
    if (shutters == True):
         x.nsl.shutters=[1, 2, 3, 4, 5, 6]
    else:
         x.nsl.shutters=[]
         print('Shutters are left open.')
        
    x.nsl.prex=xray_num
    x.nsl.during=0
    SiT(xray_trans)
    if (daq_end == True):
        p=x.nsl.shot(record=save, end_run=True)
    if (daq_end == False):
        p=x.nsl.shot(record=save, end_run=False)
    RE(p)
    if (save == True):
        RunNumber = get_run_number(hutch='mec', timeout=10)
        mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
        mecl.post(msg, run=RunNumber, tags=tags_ref)
    # restore laser rep rate in case the next action does not involve the use of the following scripts (like shots from the hutch)
    x.nsl._config['rate']=10

# method to perform XRD calibration by moving to the appropriate target and save a daq run
def xray_calib(xray_trans=0.01, xray_num=10, calibrant='CeO2', rate=1, save=False):
    '''
    Description: script to take xray only events performing an XRD calibration on calib target.
    IN:
        xray_trans : decimal value of the xray transmission
        xray_num   : number of x-rays to send on target
        calibrant  : values are 'CeO2', 'LaB6', 'Ti'
        rate       : set the configuration rate to run the DAQ, 1 is when VISAR is in the DAQ or you want to move in between shots, otherwise, it can be anything else
        save       : True to save to the DAQ, False otherwise
    OUT:
        execute the plan
    '''
    # start by moving on target
    if ((calibrant == 'CeO2') or (calibrant == 'ceo2')):
        ceo2()
        msg_calib_target = 'on CeO2'
    if ((calibrant == 'LaB6') or (calibrant == 'lab6')):
        lab6()
        msg_calib_target = 'on LaB6'
    if ((calibrant == 'Ti') or (calibrant == 'ti')):
        ti()
        msg_calib_target = 'on Ti'
    if ((calibrant == 'Cu') or (calibrant == 'cu')):
        cu()
        msg_calib_target = 'on Cu 5 mic'
    if ((calibrant == 'Zn') or (calibrant == 'zn')):
        zn()
        msg_calib_target = 'on Zn 2.5 mic'
    # use 10Hz rep rate to get calibration shots only when visar is not in the DAQ
    # use 1Hz rep rate to get calibration shots only when visar is in the DAQ
    x.nsl._config['rate']=rate
    x.nsl.predark=1
    x.nsl.prex=xray_num
    x.nsl.during=0
    SiT(xray_trans)
    p=x.nsl.shot(record=save, ps=False)
    RE(p)
    RunNumber = get_run_number(hutch='mec', timeout=10)
    # experimentName: global variable fro mec.beamline:
    mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
    msg = '{} x-ray only shots at {:.1f}% {}.'.format(xray_num, 100.0 * xray_trans, msg_calib_target)
    mecl.post(msg, run=RunNumber, tags=['xray', 'calibration', calibrant])
    # until we can easily know if the VISAR is in the DAQ, it forces the rate back to 1 Hz
    x.nsl._config['rate']=1


# method to perform a pump-probe LPL shot
def optical_shot(lpl_ener=1.0, timing=0.0e-9, xray_trans=1, prex=0, daq_end=True, msg='', arms='all', tags_words=['optical', 'sample'], auto_trig=False, auto_charge=False, visar=True):
    '''
    Description: script to shoot the optical laser and time it with the xrays. It automatically push to the elog the laser energy, the timing and the xray SiT transmission.
    IN:
        lpl_ener   : waveplate settings for the lpl energy, decimal value, meaning 1. = 100%, 0.5 = 50%
        timing     : moves absolute, in s
        xray_trans : X ray transmission, meaning 1. = 100%, 0.5 = 50%
        msg        : message to post to the elog
        arms       : all, ABGH, EFIJ are valid
        tags_words : accompagnying tags to the elog
        prex       : when True, allows to take one Xray or visar reference
        daq_persistent: if True, it will allow the DAQ to keep the data on screen until daq.disconnect() is used.
        auto_trig  : True to make sure the triggers are enabled, False otherwise (simulation test for example).False by default.
        auto_charge: True to charge automatically the PFN. False by default.
        visar      : True to check that the VISAR triggers are set properly.
    OUT:
        execute the plan and post a comment to the elog.
    '''
    # make sure the daq is not connected before starting the command
    if (daq.connected == True):
        daq.disconnect()
    # charging process
    if ((arms == 'all') or (arms == 'ABGH') or (arms == 'EFIJ') or (arms=='ABEF') or (arms=='GHIJ')):
        ARMonly(arms, set_T=lpl_ener)
        time.sleep(5)
        if (auto_charge == True):
            print("Waiting until charging is authorized ...")
            while lpl_charge_status.get()==0:
               time.sleep(1)
            if (lpl_charge_status.get() == 1):
                lpl_charge_btn.put(1)
                print('Auto charging the laser, waiting 15 sec to be completed...')
                time.sleep(15)
                print('Laser should be charged, check it!')
        else:
            print('Auto charging is disabled, make sure to press the button on the GUI!')
    # VISAR checks
    if (visar == True):
        # make sure the visar event codes are properly set
        visar_mode(status='daq')
    # to change and display the timing of the Xrays vs the LPL
    nstiming.mv(timing)
    nstiming.get_delay()
    # to change the Xray transmission for the driven shot
    SiT(xray_trans)
    # check the trigger status
    if (auto_trig == True):
        if (lpl_slicer_evr_btn.get() == 0):
            lpl_slicer_evr_btn.put(1)
        if (lpl_lamps_evr_btn.get() == 0):
            lpl_lamps_evr_btn.put(1)
        print('NS slicer and Lamps trigger buttons are Enabled.')
    else:
        print('NS slicer and Lamps trigger buttons are not being checked by the script.')
    # to setup the plan for a driven shot, and make sure the rate for the drive laser is 10 Hz
    x.nsl._config['rate']=10
    # force the use of the shutters as you are driving the target
    x.nsl.shutters=[1, 2, 3, 4, 5, 6]
    x.nsl.predark=0
    x.nsl.prex=prex
    x.nsl.during=1
    # to set the plan with the new configuration
    if (daq_end == True):
        p=x.nsl.shot(record=True, ps=True, end_run=True)
    if (daq_end == False):
        p=x.nsl.shot(record=True, ps=True, end_run=False)
    # to run the plan
    RE(p)
    # to save to the elog: needs to be set after the plan is exhausted otehrwise post in t3he wrong run number
    RunNumber = get_run_number(hutch='mec', timeout=10)
    mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
    msg = msg + '{} arms, laser shot {}: laser energy is at {:.1f} % from max, delay is {:.2f} ns, SiT at {:.1f} %.'.format(arms, msg_log_target, 100.0 * lpl_ener, 1.0e9 * timing, 100.0 * xray_trans)
    mecl.post(msg, run=RunNumber, tags=tags_words)
    # make sure the event sequencer is getting ready for the alignment mode of the VISAR by starting the event sequencer at 1Hz, and no need to touch the trigger as they are ready for this task
    x.start_seq(1)
    # restore the number of prex shots after the driven shot. Could restore the entire default config at some point.
    x.nsl.prex=0

# For delay line in the chamber:
# delay_line_t0 to change manually for now
# mm
delay_line_t0 = 30.0
# mm/ps
delay_line_calib = 0.149896229


def spl_timing_save_t0(): 
    '''
    Description : saving the current VITARA position to a PV
    '''
    global spl_timing_tmp
    spl_timing_tmp = spl_vitara_pv.put(spl_vitara.get()) 
    print('The timing is set at {} ns.'.format(spl_timing_tmp))

def spl_timing(mono='out', timing=0.0e-9): 
    '''
    Description : setting a new pump-probe delay
    IN          :
        mono    : defines if you want timing between mono IN or OUT
        timing  : value for the Xrays to arrive 'timing' ns later than optical laser when positive.
    '''
    global delay_line_t0, delay_line_calib
    if (mono == 'out'):
        spl_vitara.put(spl_vitara_pv.get() - (timing / 1.0e-9))
        print('Timing done with Mono OUT.')
    if (mono == 'in'):
        spl_vitara.put((spl_vitara_pv.get() + (1.116)) - (timing / 1.0e-9))
        print('Timing done with Mono IN.')
    # moving delay line:
    delay_offset = (timing / 1.0e-12) * delay_line_calib
    if (delay_offset < 47.0) and (delay_offset > -47.0):
        delay_line.mv(delay_line_t0 - delay_offset)
        print('Moved delay line to compensate for drive timing.')
    else:
        print('Cannot compensate probe delay for asked pump probe delay.')
    print('New timing is {} ns after the optical laser.'.format(timing/ 1.0e-9))

def spl_mode(mode='alignment'):
    '''
    Description: Set the uniblitz and inhibit configuration for single shot (ss), continuos 5Hz (5Hz) and alignment mode (alignment).
    IN:
        mode: ss, 5Hz, alignment
    '''
    # disable the spl slicer before changing mode
    spl_slicer_evr_btn.put(0)
    print('SPL slicer trigger button is Disabled.')
    # force disable the uniblitz triggering
    spl_uniblitz_evr_btn.put(0)
    print('SPL uniblitz trigger button is Disabled.')
    # setting uniblitz event code
    spl_uniblitz_evr_code.put(177)
    if (mode == 'alignment'):
        spl_uniblitz_65mm.put(0)
        # waiting for the 65mm uniblitz to open
        time.sleep(0.2) 
        print('Setting polarity on 65 mm uniblitz to open (negative).')
        spl_uniblitz_6mm.put(0)
        print('Setting polarity on 6 mm uniblitz to open (negative).')
        spl_uniblitz_inh.put(3)
        print('Setting inhibit channels for the 6 and 65 mm uniblitz.')
    if (mode == '5Hz'):
        spl_uniblitz_6mm.put(1)
        print('Setting polarity on 6 mm uniblitz to close (positive).')
        spl_uniblitz_65mm.put(0)
        print('Setting polarity on 65 mm uniblitz to open (negative).')
        spl_uniblitz_inh.put(2)
        print('Setting inhibit channels for the 62 mm uniblitz.')
    # force enable the uniblitz triggering
    spl_uniblitz_evr_btn.put(1)
    print('Force enabling the triggering of the uniblitz.')
    

spl_sequence = [[177, 12, 0, 0],
                [168, 10, 0, 0],
                [176,  2, 0, 0],
                [169,  0, 0, 0]]

def spl_shot(nshot=1, spl_ener=1.0, timing=0.0e-9, xray_trans=1, msg='', tags_words=['optical', 'sample'], auto_trig=True, save_data=True, freeze_daq=False):
    '''
    Description: script to shoot the optical laser and time it with the xrays. It automatically push to the elog the laser energy, the timing and the xray SiT transmission.
    IN:
        nshot      : defines the nu;ber of shots, less than 10 for bluesky3 script, otherwise evt sequencer is used
        spl_ener   : gaia timing to control the spl energy, decimal value, meaning 1. = 100%, 0.5 = 50%
        timing     : moves absolute, in s
        xray_trans : X ray transmission, meaning 1. = 100%, 0.5 = 50%
        msg        : message to post to the elog
        tags_words : accompagnying tags to the elog
        auto_trig  : True to make sure the triggers are enabled, False otherwise (simulation test for example)
        save_data  : save the data in teh DAQ if True, otherwise don't
        freeze_daq : allows to see the last run. Requires a daq.disconnect() after the shot to preprare for the next shot.
    OUT:
        execute the plan and post a comment to the elog.
    '''
    # to change the Xray transmission for the driven shot
    SiT(xray_trans)
    # set the uniblitz mode to provide 5Hz but protectred by the uniblitz. Used for all DAQ modes.
    spl_mode(mode='5Hz')
    # check the trigger status
    if (auto_trig == True):
        # look at the event code
        spl_slicer_evr_code.put(176)
        if (spl_slicer_evr_btn.get() == 0):
            spl_slicer_evr_btn.put(1)
        print('SPL slicer trigger button is Enabled.')
    else:
        print('SPL slicer trigger button is not being checked by the script.')
    if (nshot < 10):
        # to setup the plan for a driven shot, and make sure the rate for the drive laser is 10 Hz
        x.fsl._config['rate']=5
        # force the use of the shutters as you are driving the target
        x.fsl.shutters=[1, 2]
        x.fsl.prelasertrig=24
        x.fsl.predark=0
        x.fsl.prex=0
        x.fsl.during=nshot
        # to set the plan with the new configuration
        p=x.fsl.shot(record=data_record, end_run=freeze_daq)
        # to run the plan
        RE(p)
        # make sure the event sequencer is getting ready for the 'continuous' shot mode'
        x.start_seq(5)
    else:
        shutter1.close()
        shutter2.close()
        seq.sequence.put_seq(spl_sequence)
        seq.play_mode.put(1)
        seq.rep_count.put(nshot)
        daq.begin(record=save_data, events=nshot)
        seq.start()
    # to save to the elog: needs to be set after the plan is exhausted otehrwise post in t3he wrong run number
    if (save_data == True):
        RunNumber = get_run_number(hutch='mec', timeout=10)
        mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
        msg = msg + '{} laser shot(s): laser energy is at {:.1f} % from max, delay is {:.2f} ns, SiT at {:.1f} %.'.format(nshot, 100.0 * spl_ener, 1.0e9 * timing, 100.0 * xray_trans)
        mecl.post(msg, run=RunNumber, tags=tags_words)

alignment_mode = [[168, 22, 0, 0],[169,  2, 0, 0]]


def pulse_picker(rate=5):
        # reset the mode for the pp
        pp.put(0)
        # set the flip/flop mode
        pp.put(2)
        # push the sequence
        seq.sequence.put_seq(alignment_mode)
        seq.play_mode.put(2)
        seq.start()
    



# rolling status definitions
def ps():
    print("Stopper 2 : "+sh2.position )
    print("Stopper 6 : "+sh6.position )
    print("reflaser (1.0 is IN) :" +str(ref_y.position))
    print("yag0 : "+yag0.position)
    print("yag1 : "+yag1.position)
    print("yag2 : "+yag2.position)
    print("yag3 : "+yag3.position)
    print("pulse picker : "+mec_pulsepicker.position)
    print("at1l0 transmission : " +str(at1l0.position))
    print("at2l0 transmission : " +str(at2l0.position))
    print("Si transmission : "+str(SiT()))
    print("slit 1 : "+str(slit1.position))
    print("slit 2 : "+str(slit2.position))
    print("slit 3 : "+str(slit3.position))
    print("slit 4 : "+str(slit4.position))
    print("IPMs : UNKNOWN POSITION")
    print("BE lens position : "+str(be_lens_stack.get()))
    print("HRM : UNKNOWN POSITION")
    print("******************************************************")
    print("Shutter 1 open : "+str(shutter1.isopen))
    print("Shutter 2 open : "+str(shutter2.isopen))
    print("Shutter 3 open : "+str(shutter3.isopen))
    print("Shutter 4 open : "+str(shutter4.isopen))
    print("Shutter 5 open : "+str(shutter5.isopen))
    print("Shutter 6 open : "+str(shutter6.isopen))

def rs():
    while True:
        time.sleep(1)
        print("STATUS at "+str(datetime.now()))
        print("******************************************************")
        ps()
        print("******************************************************")

# presets definitions
#def motor_wait(motor=None, value=None):
#    delta = 0.1
#    print('Moving...')
#    if (motor == tgx):
#        while ((motor.position <= (value - delta)) and (motor.position >= (value + delta))):
#            time.sleep(0.2)
#    else:
#        while ((motor.get() <= (value - delta)) and (motor.get() >= (value + delta))):
#            print('in')
#            time.sleep(0.2)
#        print('out', motor, motor.get())
#    print('Motor {} reached destination.'.format(motor))
    
def tg_pin():
    arr = load_presets()
    # force going down before any motion
    tgy.put(0)
    time.sleep(7)
    tgx.mv(arr[0])
    if (tgx.position != arr[0]):
        time.sleep(10)
        print('Motor X reached destination.')
        #motor_wait(motor=tgx, value = arr[0])
    tgy.put(arr[1])
    if (tgy_rbv.get() != arr[1]):
        time.sleep(10)
        print('Motor Y reached destination.')
        #motor_wait(motor=tgy_rbv, value = arr[1])
    tgz.put(arr[2])
    print('Motor Z reached destination.')
    #motor_wait(motor=tgz_rbv, value = arr[2])

def catcher():
    arr = load_presets()
    # force going down before any motion
    tgy.put(0)
    time.sleep(7)
    tgx.mv(arr[3])
    if (tgx.position != arr[3]):
        time.sleep(10)
        print('Motor X reached destination.')
    tgy.put(arr[4])
    if (tgy_rbv.get() != arr[4]):
        time.sleep(10)
        print('Motor Y reached destination.')
    tgz.put(arr[5])
    print('Motor Z reached destination.')

def tg_gold():
    arr = load_presets()
    # force going down before any motion
    tgy.put(0)
    time.sleep(7)
    tgx.mv(arr[6])
    if (tgx.position != arr[6]):
        time.sleep(10)
        print('Motor X reached destination.')
    tgy.put(arr[7])
    if (tgy_rbv.get() != arr[7]):
        time.sleep(10)
        print('Motor Y reached destination.')
    tgz.put(arr[8])
    print('Motor Z reached destination.')

def pin():
    """ move to the pin. Uses the User pvs."""
    tgx.mv(pintgx.get())
    hexx.put(pinhx.get())
    hexy.put(pinhy.get())
    hexz.put(pinhz.get())

def pin_s():
    """ saves current position in pin user pv. Uses the User pvs."""
    pintgx.put(tgx())
    pinhx.put(hexx.get())
    pinhy.put(hexy.get())
    pinhz.put(hexz.get())

def pinhole():
    """ move to the pinhole. Uses the User pvs."""
    tgx.mv(pinholetgx.get())
    hexx.put(pinholehx.get())
    hexy.put(pinholehy.get())
    hexz.put(pinholehz.get())

def pinhole_s():
    """ saves current position in pinhole user pv. Uses the User pvs."""
    pinholetgx.put(tgx())
    pinholehx.put(hexx.get())
    pinholehy.put(hexy.get())
    pinholehz.put(hexz.get())

def ceo2():
    """ move to the CeO2 calibrant. Uses the User pvs."""
    tgx.mv(ceo2tgx.get())
    hexx.put(ceo2hx.get())
    hexy.put(ceo2hy.get())
    hexz.put(ceo2hz.get())

def ceo2_s():
    """ saves current position in CeO2 user pv. Uses the User pvs."""
    ceo2tgx.put(tgx())
    ceo2hx.put(hexx.get())
    ceo2hy.put(hexy.get())
    ceo2hz.put(hexz.get())

def lab6():
    """ move to the LaB6 calibrant. Uses the User pvs."""
    tgx.mv(lab6tgx.get())
    hexx.put(lab6hx.get())
    hexy.put(lab6hy.get())
    hexz.put(lab6hz.get())

def lab6_s():
    """ saves current position in LaB6 user pv. Uses the User pvs."""
    lab6tgx.put(tgx())
    lab6hx.put(hexx.get())
    lab6hy.put(hexy.get())
    lab6hz.put(hexz.get())

def cu():
    """ move to the Cu 5 mic calibrant. Uses the User pvs."""
    tgx.mv(cutgx.get())
    hexx.put(cuhx.get())
    hexy.put(cuhy.get())
    hexz.put(cuhz.get())

def cu_s():
    """ saves current position in Cu 5 mic user pv. Uses the User pvs."""
    cutgx.put(tgx())
    cuhx.put(hexx.get())
    cuhy.put(hexy.get())
    cuhz.put(hexz.get())

def zn():
    """ move to the Zn 2.5 mic calibrant. Uses the User pvs."""
    tgx.mv(zntgx.get())
    hexx.put(znhx.get())
    hexy.put(znhy.get())
    hexz.put(znhz.get())

def zn_s():
    """ saves current position in Zn 2.5 mic user pv. Uses the User pvs."""
    zntgx.put(tgx())
    znhx.put(hexx.get())
    znhy.put(hexy.get())
    znhz.put(hexz.get())

def ti():
    """ move to the ti sample. Uses the User pvs."""
    tgx.mv(titgx.get())
    hexx.put(tihx.get())
    hexy.put(tihy.get())
    hexz.put(tihz.get())

def ti_s():
    """ saves current position in ti user pv. Uses the User pvs."""
    titgx.put(tgx())
    tihx.put(hexx.get())
    tihy.put(hexy.get())
    tihz.put(hexz.get())

def grid():
    """ move to the grid sample. Uses the User pvs."""
    tgx.mv(gridtgx.get())
    hexx.put(gridhx.get())
    hexy.put(gridhy.get())
    hexz.put(gridhz.get())

def grid_s():
    """ saves current position in grid user pv. Uses the User pvs."""
    gridtgx.put(tgx())
    gridhx.put(hexx.get())
    gridhy.put(hexy.get())
    gridhz.put(hexz.get())

def yag():
    """ move to the yag."""
    tgx.mv(yagtgx.get())
    hexx.put(yaghx.get())
    hexy.put(yaghy.get())
    hexz.put(yaghz.get())

def yag_s():
    """ saves current position in the yag user pv. Uses the User pvs."""
    yagtgx.put(tgx())
    yaghx.put(hexx.get())
    yaghy.put(hexy.get())
    yaghz.put(hexz.get())

def diode_air():
    """ moves the 500mm stage to the in air Diode position in user pv."""
    s500mm.put(diode500mm.get())
    
def diode_air_s():
    """ Saves current position of the diode in user pvs."""
    diode500mm.put(s500mm.get())

def spectro_air():
    """ moves the 500mm stage to the in air spectrometer position in user pv."""
    s500mm.put(spectro500mm.get())
    
def spectro_air_s():
    """ Saves current position of the in air spectrometer in user pvs."""
    spectro500mm.put(s500mm.get())

def gige4():
    """ moves the 500mm stage to the in air gige4 position in user pv."""
    s500mm.put(gige4500mm.get())
    
def gige4_s():
    """ Saves current position of the gige4 in user pvs."""
    gige4500mm.put(s500mm.get())

def neo():
    """ moves the 500mm stage to the NEO position in user pv."""
    s500mm.put(neo500mm.get())
    
def neo_s():
    """ Saves current position of NEO in user pvs."""
    neo500mm.put(s500mm.get())

# target motion definition (TO DO: add target.tweakxy)
def target_up(n=1):
    """ moves up n spaces, spacing is 3.5mm"""
    hexy.put(hexy.get()+(n*3.5))

def target_down(n=1):
    """ moves down n spaces, spacing is 3.5mm"""
    target_up(-n)

def target_next(n=1):
    """ moves next n spaces, spacing is 3.7mm"""
    tgx(tgx()+(n*3.7))

def target_prev(n=1):
    """ moves previous n spaces, spacing is 3.7mm"""
    target_next(-n)

def target_return():
    """ returns target stage position to previous saved values"""
    hexx.put(targetsavehx.get())
    hexy.put(targetsavehy.get())
    hexz.put(targetsavehz.get())
    tgx(targetsavetgx.get())

def target_save():
    """ saves current target stage position in userpvs. You can go back with target_return() """
    targetsavehx.put(hexx.get())
    targetsavehy.put(hexy.get())
    targetsavehz.put(hexz.get())
    targetsavetgx.put(tgx())

# -- Definitions for the target motion using letters -------------------------
letter_arr = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
one_u = 40.2
half_u = 19.5
# x_start_pos is pin+pos - position of the first frame A1 column value
x_start_pos = 35.81
y_start_pos = -12.0
x_step = 3.7
y_step = 3.5
pin_pos = 154.5
# look from the back of the target holder, 1 is for a full U, 0.5 is for a half U, start from the left
#frame_config = [1, 1, 1]
# defining a global variable to store the current target position
msg_log_target = ''
def move_to_target(frame_cfg=[1, 'F1', 1, 'F2', 1, 'F3'], frame=1, target='A1'):
    '''
    Description: script to move to a predefined target in the target holder. Assuming 
    for now that columns are letters, and raws are numbers. Columns start from A and 
    finish at I from left to right and raws start from 1 to 7 from top to bottom. All 
    these while looking at the target holder from the back (opposite view from questar 1).

    Since everytarget frame is position a few 100um differt due to screw slop, there are two 
    epics user pv that can be set as a correction for each target. These correctionis should be 
    small (<1mm), and are best reset when going to a different frame. They are the user PVs
    57 and 58.

    IN:
        frame_cfg : the configuration of the frames on the target holder as viewed from 
                    the back, meaning the opposite view of Q1. TO DO: need to confirm size 
                    of the half-U frame.
        frame     : the number of the frame where the targets are located. Can be full size 
                    or half size U frame. TO DO: need to confirm size of the half-U frame.
        target    : the number of the target to go to within this frame.
    OUT:
        move to target
    '''
    xcorr=EpicsSignal('MEC:NOTE:DOUBLE:57').get()
    ycorr=EpicsSignal('MEC:NOTE:DOUBLE:58').get()

    # 1U is 40mm large, 0.5U is 20mm, starting from just after the calibration cartridge
    global msg_log_target
    frame_pos = x_start_pos 
    if (frame > 1):
	# -1 to not account for the first frame, and count for the other position in the array
        for idx in np.arange(0, 2*(frame-1), 2):
            if (frame_cfg[idx] == 1):
                frame_pos = frame_pos + one_u
            else:
                frame_pos = frame_pos + half_u
    # starting position from where the target value will be evaluated
    # +1 because the array start
    target_col = letter_arr.index(target[0])+1
    target_raw = int(target[1])
    # initialisation of x and y target positions
    y_target_pos = y_start_pos
    x_target_pos = 0.0
    # calculating the y position of the target
    if (target_raw > 1):
        y_target_pos = y_target_pos + ((target_raw - 1) * y_step)
    # calculatinf the x position of the target
    if (target_col > 1):
        x_target_pos = x_target_pos + ((target_col - 1) * x_step)
    # execute the motion
    tgx(pin_pos - (x_target_pos + frame_pos) + xcorr)
    hexy.put(y_target_pos + ycorr)
    print('Moving to Frame {}, target {}.'.format(frame, target))
    print('Tweak position as appropriate.')
    print('The frame configuration is {}.'.format(frame_cfg))
    # print in the eLog only the naming used by the users to avoid confusion
    msg_log_target = 'on frame {}, target {}'.format(frame_cfg[(2*frame)-1], target)
# -----------------------------------------------------------------------------

# shutters definitions
def shutters_close():
    shutter1.close()
    shutter2.close()
    shutter3.close()
    shutter4.close()
    shutter5.close()
    shutter6.close()

def shutters_open():
    shutter1.open()
    shutter2.open()
    shutter3.open()
    shutter4.open()
    shutter5.open()
    shutter6.open()

# dictionary for visar 1 and 2 PV names used to store the streak window timing. Gives the window in sec.
visar_window_pv = {\
'visar1_2ns':EpicsSignal('MEC:NOTE:VIS:CAM1_DELAY2d0'),
'visar1_5ns':EpicsSignal('MEC:NOTE:VIS:CAM1_DELAY5d0'),
'visar1_10ns':EpicsSignal('MEC:NOTE:VIS:CAM1_DELAY10d'),
'visar1_20ns':EpicsSignal('MEC:NOTE:VIS:CAM1_DELAY20d'),
'visar1_50ns':EpicsSignal('MEC:NOTE:VIS:CAM1_DELAY50d'),
'visar1_100ns':EpicsSignal('MEC:NOTE:VIS:CAM1_DELAY100'),
'visar1_200ns':EpicsSignal('MEC:NOTE:VIS:CAM1_DELAY200'),
'visar2_2ns':EpicsSignal('MEC:NOTE:VIS:CAM2_DELAY2d0'),
'visar2_5ns':EpicsSignal('MEC:NOTE:VIS:CAM2_DELAY5d0'),
'visar2_10ns':EpicsSignal('MEC:NOTE:VIS:CAM2_DELAY10d'),
'visar2_20ns':EpicsSignal('MEC:NOTE:VIS:CAM2_DELAY20d'),
'visar2_50ns':EpicsSignal('MEC:NOTE:VIS:CAM2_DELAY50d'),
'visar2_100ns':EpicsSignal('MEC:NOTE:VIS:CAM2_DELAY100'),
'visar2_200ns':EpicsSignal('MEC:NOTE:VIS:CAM2_DELAY200')}    

# dictionnary of the streak window as per the GUI. Second number is streak window in ns.
visar_window_remote = {0:0.5, 1:1, 2:2, 3:5, 4:10, 5:20, 6:50, 7:100, 8:200, 9:500, 10:1000, 11:2000, 12:5000, 13:10000, 14:20000, 15:50000}

# getting the visar streak windows and the values from the timing box
visar1_window = EpicsSignal('MEC:STREAK:01:TimeRange')
visar2_window = EpicsSignal('MEC:STREAK:02:TimeRange')
visar1_dgbox = EpicsSignal('MEC:LAS:DDG:05:aDelayAO')
visar2_dgbox = EpicsSignal('MEC:LAS:DDG:05:cDelayAO')

def streak_timing_status(verbose=False, save=False):
    '''
    Description: displays the status of the timing configuration for both VISAR system. It will require to have the Xremote up and running.
    IN:
        verbose : add some more info on the timing configuration.
        save    : push the entire current configuration to the elog.
    OUT:
        displays timing info for the VISAR system
    ''' 
    # getting the visar streak window
    visar1_current_window = visar1_window.get()
    visar2_current_window = visar2_window.get()

    msg = ''
    # getting the saved delays for eah visar windows.
    for j in range(1, 3):
        tmp_chr = 'Visar {} timing:'.format(str(j))
        msg = msg + '\n' + tmp_chr
        if (verbose == True):
            print(tmp_chr)
        for i in range(2, 9):
            val = visar_window_remote[i]
            tmp_chr = '{:3d} ns window, {:.12f} ns delay'.format(val, visar_window_pv['visar'+str(j)+'_'+str(val)+'ns'].get())
            msg = msg + '\n' + tmp_chr
            if (verbose == True):
                print(tmp_chr)
        if (verbose == True):
            print('')
        msg = msg + '\n'

    # get the current streak delay, if any, at the current streak window 
    visar1_delay = visar1_dgbox.get() - visar_window_pv['visar1_'+str(visar_window_remote[visar1_current_window])+'ns'].get()
    visar2_delay = visar2_dgbox.get() - visar_window_pv['visar2_'+str(visar_window_remote[visar2_current_window])+'ns'].get()

    # get the current windows used in the streak cameras. It reauires the xremote to be running.
    tmp_chr = 'VISAR 1 current streak window configuration:'
    msg = msg + '\n' + tmp_chr
    print(tmp_chr)
    tmp_chr = ' > Window length: {} ns.'.format(visar_window_remote[visar1_current_window])
    msg = msg + '\n' + tmp_chr
    print(tmp_chr)
    tmp_chr = ' > Timing offset: {:.2f} ns.'.format(1.0e9*visar1_delay)  # convert from s to ns
    msg = msg + '\n' + tmp_chr
    print(tmp_chr)
    tmp_chr = ''
    msg = msg + '\n' + tmp_chr
    print(tmp_chr)
    tmp_chr = 'VISAR 2 current streak window configuration:'
    msg = msg + '\n' + tmp_chr
    print(tmp_chr)
    tmp_chr = ' > Window length: {} ns.'.format(visar_window_remote[visar2_current_window])
    msg = msg + '\n' + tmp_chr 
    print(tmp_chr)
    tmp_chr = ' > Timing offset: {:.2f} ns.'.format(1.0e9*visar2_delay)  # convert from s to ns
    msg = msg + '\n' + tmp_chr
    print(tmp_chr)

    # push the current status to the elog
    if (save == True):
        mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
        mecl.post(msg, run=None, tags=['visar', 'configuration', 'timing'])
        

def streak_window(visar=1, window=None, offset=0):
    '''
    Description: allows to change the VISAR streak window and/or add an offset to the current visar streak window.
    IN:
        visar   : the number of the visar to consider, 1 and 2.
        window  : set the visar window, in ns, valid entries are 2, 5, 10, 20, 50, 100 and 200. If no window is provided, the current window is used.
        offset  : delay in ns to add to the current window settings.
    OUT:
        push the offset to the DGbox
    '''
    # get the current visar streak window, in ns
    visar1_window_saved = visar_window_remote[visar1_window.get()]
    visar2_window_saved = visar_window_remote[visar2_window.get()]
    # get the current offset
    visar1_offset_saved = visar1_dgbox.get() - visar_window_pv['visar1_' + str(visar1_window_saved)+ 'ns'].get()
    visar2_offset_saved = visar2_dgbox.get() - visar_window_pv['visar2_' + str(visar2_window_saved)+ 'ns'].get()

    if (window is not None):
    # if a number is used, set the window to this value
        key_list = list(visar_window_remote.keys())
        val_list = list(visar_window_remote.values())
        position = val_list.index(window)
        if (visar == 1):
            visar1_window_selected = window
            try:
                daq.disconnect()
                daq.stop()
            except:
                print('If the DAQ is running, failed to put it in "Shutdown" mode. Please do it manually, otherwise ignore.')
            visar1_window.set(key_list[position])
        if (visar == 2):
            visar2_window_selected = window
            try:
                daq.disconnect()
                daq.stop()
            except:
                print('If the DAQ is running, failed to put it in "Shutdown" mode. Please do it manually, otherwise ignore.')
            visar2_window.set(key_list[position])

    if (visar == 1):
        print('VISAR 1 previous configuration:')
        print(' > Window length: {:.2f} ns.'.format(visar1_window_saved))
        print(' > Timing offset: {:.2f} ns.'.format(1.0e9*visar1_offset_saved)) # convert from s to ns
        print('')
        if (window is not None):
            channel_val = visar_window_pv['visar1_'+str(visar1_window_selected)+'ns'].get()
        else:
            channel_val = visar_window_pv['visar1_'+str(visar1_window_saved)+'ns'].get()
        channel_val = channel_val + (1.0e-9 * offset)
        visar1_dgbox.set(channel_val)
        print('VISAR 1 new configuration:')
        if (window is not None):
            print(' > Window length: {:.2f} ns.'.format(window))
        else:
            print(' > Window length: {:.2f} ns.'.format(visar1_window_saved))
        print(' > Timing offset: {:.2f} ns.'.format(offset)) # convert from s to ns
    if (visar == 2):
        print('VISAR 2 previous configuration:')
        print(' > Window length: {:.2f} ns.'.format(visar2_window_saved))
        print(' > Timing offset: {:.2f} ns.'.format(1.0e9*visar2_offset_saved)) # convert from s to ns
        print('')
        if (window is not None):
            channel_val = visar_window_pv['visar2_'+str(visar2_window_selected)+'ns'].get()
        else:
            channel_val = visar_window_pv['visar2_'+str(visar2_window_saved)+'ns'].get()
        channel_val = channel_val + (1.0e-9 * offset)
        visar2_dgbox.set(channel_val)
        print('VISAR 2 new configuration:')
        if (window is not None):
            print(' > Window length: {:.2f} ns.'.format(window))
        else:
            print(' > Window length: {:.2f} ns.'.format(visar2_window_saved))
        print(' > Timing offset: {:.2f} ns.'.format(offset)) # convert from s to ns

def streak_save(visar=1, window=10):
    '''
    Description: use this command to save timing information for the VISAR window into a designated PV value.
    IN:
        visar   : number of the visar, valid values are 1 and 2.
        window  : the window size for which the timing is being added, in ns, valid entries are 2, 5, 10, 20, 50, 100 and 200.
    OUT:
        push the current timing from a DGbox channel to the right PV value.
    '''
    if (visar == 1):
        visar_window_pv['visar' + str(visar) + '_' + str(window) + 'ns'].set(visar1_dgbox.get())
        print('{:.12f} s has been saved for VISAR 1, window {} ns.'.format(visar1_dgbox.get(), window))
    if (visar == 2):
        visar_window_pv['visar' + str(visar) + '_' + str(window) + 'ns'].set(visar2_dgbox.get())
        print('{:.12f} s has been saved for VISAR 2, window {} ns.'.format(visar2_dgbox.get(), window))

