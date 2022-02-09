from bluesky.plans import count, scan, list_scan
import bluesky.plan_stubs as bps
import time

from pcdsdaq.preprocessors import daq_during_decorator
from bluesky.preprocessors import run_decorator

from pcdsdevices.epics_motor import Motor
from ophyd.pv_positioner import PVPositioner
from ophyd.device import FormattedComponent as FCpt
from ophyd.signal import EpicsSignal, EpicsSignalRO

from mec.db import seq, daq
from mec.db import mec_pulsepicker as pp
from mec.db import shutter1, shutter2, shutter3, shutter4, shutter5, shutter6
from mec.db import target
from mec.sequence import Sequence
from mec.laser import FemtoSecondLaser, NanoSecondLaser

from mecps import *

import logging 
logger = logging.getLogger(__name__)

class User():

    target_x = Motor('MEC:USR:MMS:17', name='target_x_motor')

    YFEon = YFEon
    YFEoff = YFEoff
    HWPon = HWPon
    SHG_opt = SHG_opt
    save_scope_to_eLog = save_scope_to_eLog

    def start_seq(self, rate=120, wLPLaser=False):
        if rate==120:
            sync_mark = 6#int(_sync_markers[120])
        elif rate==60:
            sync_mark = 5
        elif rate==30:
            sync_mark = 4
        elif rate==10:
            sync_mark = 3
        elif rate==5:
            sync_mark = 2
        elif rate==1:
            sync_mark = 1
        elif rate==0.5:
            sync_mark = 0
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(2) # Run sequence forever
        ff_seq = [[169, 0, 0, 0]]
        if wLPLaser:
            ff_seq.append([182, 0, 0, 0])
        seq.sequence.put_seq(ff_seq)
        seq.start()

    _seq = Sequence()
    _sync_markers = {0.5:0, 1:1, 5:2, 10:3, 30:4, 60:5, 120:6, 360:7}

    nsl = NanoSecondLaser()
    fsl = FemtoSecondLaser()

    shutters = [1,2,3,4,5,6]
    _shutters = {1: shutter1,
                 2: shutter2,
                 3: shutter3,
                 4: shutter4,
                 5: shutter5,
                 6: shutter6}

    seq_a_pvs = [EpicsSignal('MEC:ECS:IOC:01:EC_6:00'),
                 EpicsSignal('MEC:ECS:IOC:01:EC_6:01'),
                 EpicsSignal('MEC:ECS:IOC:01:EC_6:02'),
                 EpicsSignal('MEC:ECS:IOC:01:EC_6:03'),
                 EpicsSignal('MEC:ECS:IOC:01:EC_6:04'),
                 EpicsSignal('MEC:ECS:IOC:01:EC_6:05'),
                 EpicsSignal('MEC:ECS:IOC:01:EC_6:06'),
                 EpicsSignal('MEC:ECS:IOC:01:EC_6:07'),
                 EpicsSignal('MEC:ECS:IOC:01:EC_6:08'),
                 EpicsSignal('MEC:ECS:IOC:01:EC_6:09')]

    seq_b_pvs = [EpicsSignal('MEC:ECS:IOC:01:BD_6:00'),
                 EpicsSignal('MEC:ECS:IOC:01:BD_6:01'),
                 EpicsSignal('MEC:ECS:IOC:01:BD_6:02'),
                 EpicsSignal('MEC:ECS:IOC:01:BD_6:03'),
                 EpicsSignal('MEC:ECS:IOC:01:BD_6:04'),
                 EpicsSignal('MEC:ECS:IOC:01:BD_6:05'),
                 EpicsSignal('MEC:ECS:IOC:01:BD_6:06'),
                 EpicsSignal('MEC:ECS:IOC:01:BD_6:07'),
                 EpicsSignal('MEC:ECS:IOC:01:BD_6:08'),
                 EpicsSignal('MEC:ECS:IOC:01:BD_6:09')]

    def open_shutters(self):
        print("Opening shutters...")
        for shutter in self.shutters:
            self._shutters[shutter].open()
        time.sleep(5)

    def close_shutters(self):
        print("Closing shutters...")
        for shutter in self.shutters:
            self._shutters[shutter].close()
        time.sleep(5)

    def seq_wait(self):
        time.sleep(0.5)
        while seq.play_status.get() != 0:
            time.sleep(0.5)

    def scalar_sequence_write(self, s):
        for i in range(len(s)):
            self.seq_a_pvs[i].put(s[i][0])
        for j in range(len(s)):
            self.seq_b_pvs[j].put(s[j][1])

        seq.sequence_length.put(len(s))

