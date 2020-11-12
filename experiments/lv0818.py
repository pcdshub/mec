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

    _seq = Sequence()
    _sync_markers = {0.5:0, 1:1, 5:2, 10:3, 30:4, 60:5, 120:6, 360:7}

    shutters = [1,2,3,4,5,6]
    _shutters = {1: shutter1,
                 2: shutter2,
                 3: shutter3,
                 4: shutter4,
                 5: shutter5,
                 6: shutter6}

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

    def shot(self, prex=0, postx=0, during=True, record=True, lasps=True):
        """
        Returns a BlueSky plan to take an optical (optionally with x-rays)
        laser shot. Intended for use with the long pulse laser. Will take a
        single optical shot.
        
        Parameters:
        -----------
        prex : int <default: 0>
            The number of pre-optical x-ray shots that you would like to take
            in the run.

        postx : int <default: 0>
            The number of post-optical x-ray shots that you would like to take
            in the run.

        during : bool <default: True>
            Flag to include x-rays with the optical shot. If True, x-rays will
            accompany the optical shot. If False, the optical shot will not
            be accompanied by x-rays.

        record : bool <default: True>
            Flag to record the data (or not).

        lasps : bool <default: True>
            Flag to perform pre-and post shot pulse shaping routines. 
        """
        logging.debug("Calling User.shot with parameters:")
        logging.debug("prex: {}".format(prex))        
        logging.debug("postx: {}".format(postx))        
        logging.debug("record: {}".format(record))        
        logging.debug("lasps: {}".format(lasps))        

        print("Configuring DAQ...")
        daq.configure(events=0, record=record) # run infinitely, let sequencer
                                               # control number of events
        
        print("Configuring sequencer...")
        # Setup the pulse picker for single shots in flip flop mode
        pp.flipflop(wait=True)
        # Setup sequencer for requested rate
        sync_mark = int(self._sync_markers[10])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(0) # Run once
        # Setup sequence
        self._seq.rate = 10

        if lasps:
            print("Running mecps.pspreshot()...")
            pspreshot()

        # Build up sequence
        s = []
        # Pre-x shots
        for i in range(prex):
            s += self._seq.darkXraySequence(1)
        # Optical shot
        if during:
            s += self._seq.duringSequence(1, 'longpulse')
        else:
            s += self._seq.opticalSequence(1, 'longpulse')
        # Post-x shots
        for i in range(postx):
            s += self._seq.darkXraySequence(1)

        seq.sequence.put_seq(s)

        # close the shutters specified by the user
        for shutter in self.shutters:
            self._shutters[shutter].close()
        # Shutters are slow; give them time to close
        time.sleep(5)

        yield from bps.trigger_and_read([daq, seq])

        daq.end_run()

        if lasps:
            print("Running mecps.pspostshot()...")
            pspostshot()

        # open the shutters specified by the user
        for shutter in self.shutters:
            self._shutters[shutter].open()
