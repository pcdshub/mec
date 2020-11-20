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

from dev.pulseshaping.mecps.mecps import pspreshot, pspostshot

import logging 
logger = logging.getLogger(__name__)

class User():

    target_x = Motor('MEC:USR:MMS:17', name='target_x_motor')

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

    def start_seq_120Hz(self):
        #self.start_seq_120Hz(120)
        sync_mark = 6#int(_sync_markers[120])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(2) # Run sequence forever
        ff_seq = [[169, 0, 0, 0]]
        seq.sequence.put_seq(ff_seq)
        seq.start()

    def start_seq_10Hz(self, wLPLaser=False):
        sync_mark = 3#int(_sync_markers[10])
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

    def uxi_shot(self, delta=0.3, record=True, lasps=True):
        """
        Returns a BlueSky plan to run a scan for the LV08 experiment. Used for
        the UXI camera which requires near continuous acquisition for stable
        camera behavior. The following shots are combined in a single run.

        Shot sequence:
        --------------
        1) 10 dark frames    # Warm up camera
        2) 10 X-ray frames
        3) Sample moves in
        4) 10 dark frames    # Warm up camera
        5) 1 X-ray + Optical laser frame
        6) 10 dark frames
        7) Sample moves out
        8) 10 dark frames    # Warm up camera
        9) 10 X-ray frames
        
        Parameters:
        -----------
        delta : float <default: 0.3>
            The relative distance in mm to move the sample in and out.

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
        sync_mark = int(self._sync_markers[0.5])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(1) # Run N times
        seq.play_count.put(10) 
        # Setup sequence
        self._seq.rate = 0.5

        # close the shutters specified by the user
        for shutter in self.shutters:
            self._shutters[shutter].close()
        # Shutters are slow; give them time to close
        time.sleep(5)

        if lasps:
            print("Running mecps.pspreshot()...")
            pspreshot()

        # Run 10 Pre-laser dark shots (step 1 above)
        s = self._seq.darkSequence(1, preshot=False)
        seq.sequence.put_seq(s)
        seq.sequence.put_seq(s) # Try double .put() to fix sequencer bug
        print("Taking 10 dark shots...")
        yield from bps.trigger_and_read([daq, seq])

        # Run 10 Pre-laser x-ray shots (step 2 above)
        s = self._seq.darkXraySequence(1, preshot=False)
        seq.sequence.put_seq(s)
        seq.sequence.put_seq(s) # Try double .put() to fix sequencer bug
        print("Taking 10 x-ray shots...")
        yield from bps.trigger_and_read([daq, seq])
        
        # Move sample in (step 3 above)
        print("Moving sample in...")
        yield from bps.mvr(self.target_x, delta) #TODO Check direction

        # Run 10 Pre-laser dark shots (step 4 above)
        print("Taking 10 dark shots...")
        s = self._seq.darkSequence(1, preshot=False)
        seq.sequence.put_seq(s)
        seq.sequence.put_seq(s) # Try double .put() to fix sequencer bug
        yield from bps.trigger_and_read([daq, seq])

        # Run x-ray + optical sequence (step 5 above)
        print("Taking optical laser shots...")
        seq.play_count.put(1) 
        s = self._seq.duringSequence(1, 'longpulse')
        seq.sequence.put_seq(s)
        seq.sequence.put_seq(s) # Try double .put() to fix sequencer bug
        yield from bps.trigger_and_read([daq, seq])

        # Run 10 Post-laser dark shots (step 6 above)
        print("Taking 10 dark shots...")
        seq.play_count.put(10) 
        s = self._seq.darkSequence(1, preshot=False)
        seq.sequence.put_seq(s)
        seq.sequence.put_seq(s) # Try double .put() to fix sequencer bug
        yield from bps.trigger_and_read([daq, seq])

        # Move sample out (step 7 above)
        print("Moving sample out...")
        yield from bps.mvr(self.target_x, -delta) #TODO Check direction

        # Run 10 Pre-x-ray dark shots (step 8 above)
        print("Taking 10 dark shots...")
        seq.play_count.put(10) 
        s = self._seq.darkSequence(1, preshot=False)
        seq.sequence.put_seq(s)
        seq.sequence.put_seq(s) # Try double .put() to fix sequencer bug
        yield from bps.trigger_and_read([daq, seq])

        # Run 10 Pre-laser x-ray shots (step 9 above)
        print("Taking 10 x-ray shots...")
        s = self._seq.darkXraySequence(1, preshot=False)
        seq.sequence.put_seq(s)
        seq.sequence.put_seq(s) # Try double .put() to fix sequencer bug
        yield from bps.trigger_and_read([daq, seq])

        daq.end_run()

        if lasps:
            print("Running mecps.pspostshot()...")
            pspostshot()

        # open the shutters specified by the user
        for shutter in self.shutters:
            self._shutters[shutter].open()
