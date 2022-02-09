#import logging

import time
from datetime import datetime
#from mec.laser import NanoSecondLaser


import elog
import pickle

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

ceo2hx=EpicsSignal('MEC:NOTE:DOUBLE:28')
ceo2hy=EpicsSignal('MEC:NOTE:DOUBLE:29')
ceo2hz=EpicsSignal('MEC:NOTE:DOUBLE:30')
ceo2tgx=EpicsSignal('MEC:NOTE:DOUBLE:31')

lab6hx=EpicsSignal('MEC:NOTE:DOUBLE:32')
lab6hy=EpicsSignal('MEC:NOTE:DOUBLE:33')
lab6hz=EpicsSignal('MEC:NOTE:DOUBLE:34')
lab6tgx=EpicsSignal('MEC:NOTE:DOUBLE:35')






def xray_only(xray_trans=1, xray_num=10, save=False):
    '''
    script to take xray only events
    IN:
       xray_trans : decimla value of the xray transmission
       record     : True to save to the DAQ, False otherwise
    OUT:
       execute the plan
    '''
    x.nsl.predark=1
    x.nsl.prex=xray_num
    x.nsl.during=0
    SiT(xray_trans)
    p=x.nsl.shot(record=save)
    RE(p)

def optical_shot(lpl_ener=1.0, timing=0.0e-9, xray_trans=1, msg='template', tags_words=['sample']):
    '''
    script to shoot the optical laser and time it with the xrays
    lpl_ener   : waveplate settings for the lpl energy, decimal value, meaning 1. = 100%, 0.5 = 50%
    timing     : moves absolute, in s
    xray_trans : X ray transmission, meaning 1. = 100%, 0.5 = 50%
    msg        : message to post to the elog
    tags_words : accompagnying tags to the elog
    '''
    # to change the energy of the LPL
    HWPon('all', set_T=lpl_ener)
    # to change and display the timing of the Xrays vs the LPL
    nstiming.mv(timing)
    nstiming.get_delay()
    # to change the Xray transmission for the driven shot
    SiT(xray_trans)
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
    mecl.post(msg, run=RunNumber, tags=tags_words)





def test():
    print("test")


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


def ceo2():
    """ move to the yag."""
    tgx.mv(ceo2tgx.get())
    hexx.put(ceo2hx.get())
    hexy.put(ceo2hy.get())
    hexz.put(ceo2hz.get())

def ceo2_s():
    """ saves current position in the yag user pv. Uses the User pvs."""
    
    ceo2tgx.put(tgx())
    ceo2hx.put(hexx.get())
    ceo2hy.put(hexy.get())
    ceo2hz.put(hexz.get())


def lab6():
    """ move to the yag."""
    tgx.mv(lab6tgx.get())
    hexx.put(lab6hx.get())
    hexy.put(lab6hy.get())
    hexz.put(lab6hz.get())

def lab6_s():
    """ saves current position in the yag user pv. Uses the User pvs."""
    
    lab6tgx.put(tgx())
    lab6hx.put(hexx.get())
    lab6hy.put(hexy.get())
    lab6hz.put(hexz.get())



def neo():
    """ moves the 500mm stage to the NEO position in user pv."""
    s500mm.put(neo500mm.get())
    
def neo_s():
    """ Saves current neo position in user pvs."""
    neo500mm.put(s500mm.get())
    
    


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

    



def gdet():
    os.system("/reg/neh/operator/mecopr/bin/gas_detector_striptool -f")

def w8():
    os.system("/reg/neh/operator/mecopr/bin/w8_detector_striptool -f")


def gigefix():
    os.system("/reg/neh/operator/mecopr/scripts/mecgigefix")

