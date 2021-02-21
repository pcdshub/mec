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

from ophyd import EpicsSignal 

#logger = logging.getLogger(__name__)

#thz_motor = Motor('MEC:USR:MMS:17', name='thz_motor')
#spl_motor = Motor('MEC:USR:MMS:17', name='spl_motor')
ref_y = Motor('MEC:XT1:MMS:01', name='ref_y')
tgx=Motor('MEC:USR:MMS:17', name='tgx')
hexy=EpicsSignal('MEC:HEX:01:Ypr')
hexx=EpicsSignal('MEC:HEX:01:Xpr')
hexz=EpicsSignal('MEC:HEX:01:Zpr')
s500mm=EpicsSignal('MEC:PPL:MMN:13')

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

neo500mm=EpicsSignal('MEC:NOTE:DOUBLE:23')

pinholehx=EpicsSignal('MEC:NOTE:DOUBLE:24')
pinholehy=EpicsSignal('MEC:NOTE:DOUBLE:25')
pinholehz=EpicsSignal('MEC:NOTE:DOUBLE:26')
pinholetgx=EpicsSignal('MEC:NOTE:DOUBLE:27')

targetsavehx=EpicsSignal('MEC:NOTE:DOUBLE:37')
targetsavehy=EpicsSignal('MEC:NOTE:DOUBLE:38')
targetsavehz=EpicsSignal('MEC:NOTE:DOUBLE:39')
targetsavetgx=EpicsSignal('MEC:NOTE:DOUBLE:40')

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

# method to prepare for visar alignment
def visar_mode(status = 'ready'):
    '''
    Description: get the VISAR triggering system ready for alignment or shot, changing the visar laser and streak camera EVR. It will force the evr button to be enabled.
    IN:
        status: 'ready' for laser shot (182), 'align' for alignment mode (43 and 44)
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
    # look at the button status (enabled:1 or diabled:0)
    if (visar_streak_evr_btn.get() == 0):
        visar_streak_evr_btn.put(1)
    if (visar_laser_evr_btn.get() == 0):
        visar_laser_evr_btn.put(1)


# method to save multiple xray only shots
def xray_only(xray_trans=1, xray_num=10, save=False):
    '''
    Description: script to take xray only events.
    IN:
        xray_trans : decimla value of the xray transmission
        xray_num   : number of x-rays to send on target
        save       : True to save to the DAQ, False otherwise
    OUT:
        execute the plan
    '''
    x.nsl.predark=1
    x.nsl.prex=xray_num
    x.nsl.during=0
    SiT(xray_trans)
    p=x.nsl.shot(record=save)
    RE(p)
    ExpName = get_curr_exp()
    RunNumber = get_run_number(hutch='mec', timeout=10)
    mecl = elog.ELog({'experiment':ExpName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
    msg = '{} x-ray only shots at {:.1f}% {}'.format(xray_num, 100.0 * xray_trans, msg_log_target)
    mecl.post(msg, run=RunNumber, tags=['xray'])


# method to perform a pump-probe LPL shot
def optical_shot(lpl_ener=1.0, timing=0.0e-9, xray_trans=1, msg='', tags_words=['optical', 'sample'], auto_trig=False, auto_charge=False):
    '''
    Description: script to shoot the optical laser and time it with the xrays. It automatically push to the elog the laser energy, the timing and the xray SiT transmission.
    IN:
        lpl_ener   : waveplate settings for the lpl energy, decimal value, meaning 1. = 100%, 0.5 = 50%
        timing     : moves absolute, in s
        xray_trans : X ray transmission, meaning 1. = 100%, 0.5 = 50%
        msg        : message to post to the elog
        tags_words : accompagnying tags to the elog
        auto_trig  : True to make sure the triggers are enabled, False otherwise (simulation test for example)
        auto_charge: True to charge automatically the PFN. False by default.
    OUT:
        execute the plan and post a comment to the elog.
    '''
    # charging process
    if (auto_charge == True):
        if (lpl_charge_status.get() == 1):
            lpl_charge_btn.put(1)
            print('Auto charging the laser, waiting 15 sec to be completed...')
            time.sleep(15)
            print('Laser should be charged, check it!')
    else:
        print('Auto charging is disabled, make sure to press the button on the GUI!')
    # to change the energy of the LPL
    HWPon('all', set_T=lpl_ener)
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
    # to setup the plan for a driven shot
    x.nsl.predark=0
    x.nsl.prex=0
    x.nsl.during=1
    # to set the plan with the new configuration
    p=x.nsl.shot(record=True, ps=True)
    # to run the plan
    RE(p)
    # to save to the elog: needs to be set after the plan is exhausted otehrwise post in t3he wrong run number
    ExpName = get_curr_exp()
    RunNumber = get_run_number(hutch='mec', timeout=10)
    mecl = elog.ELog({'experiment':ExpName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
    msg = msg + 'Laser shot {}: laser energy is at {:.1f} % from max, delay is {:.2f} ns, SiT at {:.1f} %.'.format(msg_log_target, 100.0 * lpl_ener, 1.0e9 * timing, 100.0 * xray_trans)
    mecl.post(msg, run=RunNumber, tags=tags_words)

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
    print("BE and PreFocus lens : UNKNOWN POSITION")
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

def neo():
    """ moves the 500mm stage to the NEO position in user pv."""
    s500mm.put(neo500mm.get())
    
def neo_s():
    """ Saves current neo position in user pvs."""
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
x_start_pos = 35.31
y_start_pos = -12.5
x_step = 3.7
y_step = 3.5
pin_pos = 153.6
# look from the back of the target holder, 1 is for a full U, 0.5 is for a half U, start from the left
#frame_config = [1, 1, 1]
# defining a global variable to store the current target position
msg_log_target = ''
def move_to_target(frame_cfg=[1, 'F1', 1, 'F2', 1, 'F3'], frame=1, target='A1'):
    '''
    Description: script to move to a predefined target in the target holder. Assuming for now that columns are letters, and raws are numbers. Columns start from A and finish at I from left to right and raws start from 1 to 7 from top to bottom. All these while looking at the target holder from the back (opposite view from questar 1).
    IN:
        frame_cfg : the configuration of the frames on the target holder as viewed from the back, meaning the opposite view of Q1. TO DO: need to confirm size of the half-U frame.
        frame     : the number of the frame where the targets are located. Can be full size or half size U frame. TO DO: need to confirm size of the half-U frame.
        target    : the number of the target to go to within this frame.
    OUT:
        move to target
    '''
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
    tgx(pin_pos - (x_target_pos + frame_pos))
    hexy.put(y_target_pos)
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
