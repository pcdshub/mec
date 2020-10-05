import logging
import bluesky.plan_stubs as bps
from bluesky.plans import count
import time

from pcdsdevices.epics_motor import Motor
from ophyd.pv_positioner import PVPositioner
from ophyd.device import FormattedComponent as FCpt
from ophyd.signal import EpicsSignal, EpicsSignalRO

from mec.db import seq, daq
from mec.db import mec_pulsepicker as pp
from mec.db import shutter1, shutter2, shutter3, shutter4, shutter5, shutter6
from mec.sequence import Sequence
from mec.laser import FemtoSecondLaser, NanoSecondLaser, DualLaser

logger = logging.getLogger(__name__)

thz_motor = Motor('MEC:USR:MMS:25', name='thz_motor')
spl_motor = Motor('MEC:USR:MMS:22', name='spl_motor')

class TimingChannel(object):
    def __init__(self, setpoint_PV, readback_PV, name):
        self.control_PV = EpicsSignal(setpoint_PV) # DG/Vitara PV
        self.storage_PV = EpicsSignal(readback_PV) # Notepad PV
        self.name = name

    def save_t0(self, val=None):
        """
        Set the t0 value directly, or save the current value as t0.
        """
        if not val: # Take current value to be t0 if not provided
            val = self.control_PV.get()
        self.storage_PV.put(val) # Save t0 value

    def restore_t0(self):
        """
        Restore the t0 value from the current saved value for t0.
        """
        val = self.storage_PV.get()
        self.control_PV.put(val) # write t0 value

    def mvr(self, relval):
        """
        Move the control PV relative to it's current value.
        """
        currval = self.control_PV.get()
        self.control_PV.put(currval - relval)

    def mv(self, val):
        t0 = self.storage_PV.get()
        self.control_PV.put(t0 - val)

    def get_delay(self, verbose=False):
        delay = self.control_PV.get() - self.storage_PV.get()
        if delay > 0:
            print("X-rays arrive {} s before the optical laser".format(abs(delay)))
        elif delay < 0:
            print("X-rays arrive {} s after the optical laser".format(abs(delay)))
        else: # delay is 0
            print("X-rays arrive at the same time as the optical laser")
        if verbose:
            control_data = (self.name, self.control_PV.pvname,
                            self.control_PV.get())
            storage_data = (self.name, self.storage_PV.pvname,
                            self.storage_PV.get())
            print("{} Control PV: {}, Control Value: {}".format(*control_data))
            print("{} Storage PV: {}, Storage Value: {}".format(*storage_data))

class FSTiming(object):
    def __init__(self):
        self._channel = TimingChannel('LAS:FS6:VIT:FS_TGT_TIME', 'MEC:NOTE:LAS:FST0', 'FSTiming')

    def save_t0(self, val=None):
        self._channel.save_t0(val)

    def restore_t0(self):
        self._channel.restore_t0()

    def mvr(self, relval):
        currval = self._channel.control_PV.get()
        newval = currval - (relval * 1e9) 
        self._channel.control_PV.put(newval)

    def mv(self, val):
        t0 = self._channel.storage_PV.get()
        newval = t0 - (val * 1e9) 
        self._channel.control_PV.put(newval)

    def get_delay(self, verbose=False):
        t0 = self._channel.storage_PV.get()
        currval = self._channel.control_PV.get()
        diff = t0 - currval

        if diff == 0: 
            print("Xrays are co-timed with the optical laser")
        elif diff < 0:
            print("Xrays arrive {0:.2f} fs before the optical laser".format(abs(diff*1.0e6)))
        else:
            print("Xrays arrive {0:.2f} fs after the optical laser".format(abs(diff*1.0e6)))

class NSTiming(object):
    _channels = [\
        TimingChannel('MEC:LAS:DDG:03:aDelayAO', 'MEC:NOTE:DOUBLE:41', 'chA'),
        TimingChannel('MEC:LAS:DDG:03:cDelayAO', 'MEC:NOTE:DOUBLE:42', 'chC'),
        TimingChannel('MEC:LAS:DDG:03:eDelayAO', 'MEC:NOTE:DOUBLE:43', 'chE'),
        TimingChannel('MEC:LAS:DDG:03:gDelayAO', 'MEC:NOTE:DOUBLE:44', 'chG')]

    def save_t0(self, val=None):
        for channel in self._channels:
            channel.save_t0(val)

    def restore_t0(self):
        for channel in self._channels:
            channel.restore_t0()

    def mvr(self, relval):
        for channel in self._channels:
            channel.mvr(relval)

    def mv(self, val):
        for channel in self._channels:
            channel.mv(val)

    def get_delay(self, verbose=False):
        for channel in self._channels:
            channel.get_delay(verbose=verbose)

nstiming = NSTiming()

fstiming = FSTiming()
        
def lpl_save_master_timing():
    _bkup = [\
        TimingChannel('MEC:LAS:DDG:03:aDelayAO', 'MEC:NOTE:DOUBLE:45', 'bkupA'),
        TimingChannel('MEC:LAS:DDG:03:cDelayAO', 'MEC:NOTE:DOUBLE:46', 'bkupC'),
        TimingChannel('MEC:LAS:DDG:03:eDelayAO', 'MEC:NOTE:DOUBLE:47', 'bkupE'),
        TimingChannel('MEC:LAS:DDG:03:gDelayAO', 'MEC:NOTE:DOUBLE:48', 'bkupG')]

    for channel in _bkup:
        channel.save_t0()

class User():
    thz_blocked_pos = 10.0 
    thz_passed_pos = 50.0  
    spl_blocked_pos = 5.94
    spl_passed_pos = 2.5 
    thz_motor = thz_motor
    spl_motor = spl_motor
    shutters = [1,2,3,4,5,6]
    _shutters = {1: shutter1,
             2: shutter2,
             3: shutter3,
             4: shutter4,
             5: shutter5,
             6: shutter6}

    _seq = Sequence()
    _sync_markers = {0.5:0, 1:1, 5:2, 10:3, 30:4, 60:5, 120:6, 360:7}

    nstiming = nstiming

    fstiming = fstiming

    def lpl_save_master_timing(self):
        lpl_save_master_timing()

    def open_shutters(self):
        print("Opening shutters...")
        for shutter in self.shutters:
            self._shutters[shutter].open()

    def close_shutters(self):
        print("Closing shutters...")
        for shutter in self.shutters:
            self._shutters[shutter].close()

#    def longpulse_shot(self, record=True, end_run=True):
    def longpulse_shot(self, record=True):
        """
        Returns a BlueSky plan to perform a long pulse laser shot. Collects a
        long pulse laser only shot.
        
        Parameters:
        -----------
        record : bool <default: True>
            Flag to record the data (or not).

        """
#        end_run : bool <default: True>
#            Flag to end the run after completion (or not).

        logging.debug("Calling User.longpulse_shot with parameters:")        
        logging.debug("record: {}".format(record))        
#        logging.debug("end_run: {}".format(end_run))

        print("Closing shutters...")
        for shutter in self.shutters:
            self._shutters[shutter].close()

        # Block THz generation
#        print("Blocking THz generation...")
#        yield from bps.mv(self.thz_motor, self.thz_blocked_pos, wait=True)
#
#        # Block SPL
#        print("Blocking Short Pulse...")
#        yield from bps.mv(self.spl_motor, self.spl_blocked_pos, wait=True)

        print("Configuring DAQ...")
#        daq.configure(events=1, record=record)
        daq.configure(record=record)

        print("Configuring sequencer...")
        # Setup the pulse picker for single shots in flip flop mode
        pp.flipflop(wait=True)
        # Setup sequencer for requested rate
        sync_mark = int(self._sync_markers[10])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(0) # Run sequence once
        # Setup sequence
        self._seq.rate = 10
#        s = self._seq.opticalSequence(1, 'longpulse')
        s = self._seq.duringSequence(1, 'longpulse')
        seq.sequence.put_seq(s)

        print("Now run 'daq.begin_infinite()' and press 'start' on the",
              "sequencer.")
#        yield from count([daq, seq], num=1)
#
#        if end_run:
#            time.sleep(3)
#            daq.end_run()
#
#
#        print("Opening shutters...")
#        for shutter in self.shutters:
#            self._shutters[shutter].open()

#    def xrd_cal(self, nshots=1, record=True, end_run=True):
    def xrd_cal(self, nshots=1, record=True):
        """
        Returns a BlueSky plan to perform an XRD calibration run. Collects a
        number of X-ray only shots.
        
        Parameters:
        -----------
        nshots : int <default: 1>
            The number of shots that you would like to take in the run.

        record : bool <default: True>
            Flag to record the data (or not).

        """
#        end_run : bool <default: True>
#            Flag to end the run after completion (or not).
        logging.debug("Calling User.xrd_cal with parameters:")        
        logging.debug("nshots: {}".format(nshots))        
        logging.debug("record: {}".format(record))        
#        logging.debug("end_run: {}".format(end_run))


        print("Closing shutters...")
        for shutter in self.shutters:
            self._shutters[shutter].close()

#        # Block THz generation
#        print("Blocking THz generation...")
#        yield from bps.mv(self.thz_motor, self.thz_blocked_pos, wait=True)
#
#        # Block SPL
#        print("Blocking Short Pulse...")
#        yield from bps.mv(self.spl_motor, self.spl_blocked_pos, wait=True)

#        print("Configuring DAQ...")
#        daq.configure(events=nshots, record=record)
        daq.configure(record=record)

        print("Configuring sequencer...")
        # Setup the pulse picker for single shots in flip flop mode
        pp.flipflop(wait=True)
        # Setup sequencer for requested rate
        sync_mark = int(self._sync_markers[5])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(1) # Run multiple times
        seq.rep_count.put(nshots)
        # Setup sequence
        self._seq.rate = 5
        s = self._seq.darkXraySequence(1)
        seq.sequence.put_seq(s)

        print("Now run 'daq.begin_infinite()' and press 'start' on the",
              "sequencer.")
#        yield from count([daq, seq], num=1)
#
#        if end_run:
#            time.sleep(3)
#            daq.end_run()


#        print("Opening shutters...")
#        for shutter in self.shutters:
#            self._shutters[shutter].open()

#    def ech_background(self, nshots=1, record=True, end_run=True):
    def ech_background(self, nshots=1, record=True):
        """
        Returns a BlueSky plan to perform an echelon background run. Collects a 
        number of short pulse shots with THz generation blocked. 
        
        Parameters:
        -----------
        nshots : int <default: 1>
            The number of shots that you would like to take in the run.

        record : bool <default: True>
            Flag to record the data (or not).

        """
#        end_run : bool <default: True>
#            Flag to end the run after completion (or not).

        logging.debug("Calling User.ech_background with parameters:")        
        logging.debug("nshots: {}".format(nshots))        
        logging.debug("record: {}".format(record))        
#        logging.debug("end_run: {}".format(end_run))

        print("Closing shutters...")
        for shutter in self.shutters:
            self._shutters[shutter].close()

        # Block THz generation
        print("Blocking THz generation...")
        yield from bps.mv(self.thz_motor, self.thz_blocked_pos, wait=True)

        # Block SPL
        print("Un-Blocking Short Pulse...")
        yield from bps.mv(self.spl_motor, self.spl_passed_pos, wait=True)

#        print("Configuring DAQ...")
#        daq.configure(events=nshots, record=record)
        daq.configure(record=record)

        print("Configuring sequencer...")
        # Setup the pulse picker for single shots in flip flop mode
        pp.flipflop(wait=True)
        # Setup sequencer for requested rate
        sync_mark = int(self._sync_markers[5])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(1) # Run multiple times
        seq.rep_count.put(nshots)
        # Setup sequence
        self._seq.rate = 5
        s = self._seq.opticalSequence(1, 'shortpulse')
        seq.sequence.put_seq(s)

        print("Now run 'daq.begin_infinite()' and press 'start' on the",
              "sequencer.")
#        yield from count([daq, seq], num=1)
#
#        if end_run:
#            time.sleep(3)
#            daq.end_run()

#        print("Opening shutters...")
#        for shutter in self.shutters:
#            self._shutters[shutter].open()

#    def thz_reference(self, nshots=1, record=True, end_run=True):
    def thz_reference(self, nshots=1, record=True):
        """
        Returns a BlueSky plan to perform an THz reference run. Collects a 
        number of short pulse laser shots with THz generation un-blocked. 
        
        Parameters:
        -----------
        nshots : int <default: 1>
            The number of shots that you would like to take in the run.

        record : bool <default: True>
            Flag to record the data (or not).
        """
#        end_run : bool <default: True>
#            Flag to end the run after completion (or not).

        logging.debug("Calling User.thz_reference with parameters:")        
        logging.debug("nshots: {}".format(nshots))        
        logging.debug("record: {}".format(record))        
#        logging.debug("end_run: {}".format(end_run))

        # Un-Block THz generation
        print("Un-Blocking THz generation...")
        yield from bps.mv(self.thz_motor, self.thz_passed_pos, wait=True)

        # Un-Block SPL
        print("Un-Blocking Short Pulse...")
        yield from bps.mv(self.spl_motor, self.spl_passed_pos, wait=True)

        print("Configuring DAQ...")
#        daq.configure(events=nshots, record=record)
        daq.configure(record=record)

        print("Configuring sequencer...")
        # Setup the pulse picker for single shots in flip flop mode
        pp.flipflop(wait=True)
        # Setup sequencer for requested rate
        sync_mark = int(self._sync_markers[5])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(1) # Run multiple times
        seq.rep_count.put(nshots)
        # Setup sequence
        self._seq.rate = 5
        s = self._seq.opticalSequence(1, 'shortpulse')
        seq.sequence.put_seq(s)

        print("Now run 'daq.begin_infinite()' and press 'start' on the",
              "sequencer.")
#        yield from count([daq, seq], num=1)
#
#        if end_run:
#            time.sleep(3)
#            daq.end_run()
#
#        print("Opening shutters...")
#        for shutter in self.shutters:
#            self._shutters[shutter].open()

#    def thz_drive(self, record=True, end_run=True):
    def thz_drive(self, record=True):
        """
        Returns a BlueSky plan to perform a shot with the short pulse, THz
        generation, and long pulse drive, with the XFEL. Takes a single shot.  
        
        Parameters:
        -----------
        record : bool <default: True>
            Flag to record the data (or not).

        """
#        end_run : bool <default: True>
#            Flag to end the run after completion (or not).
        logging.debug("Calling User.thz_drive with parameters:")        
        logging.debug("record: {}".format(record))        
        #logging.debug("end_run: {}".format(end_run))

        # Un-Block THz generation
        print("Un-Blocking THz generation...")
        yield from bps.mv(self.thz_motor, self.thz_passed_pos, wait=True)

        # Un-Block SPL
        print("Un-Blocking Short Pulse...")
        print("Configuring DAQ...")
        #daq.configure(events=1, record=record)
        daq.configure(record=record)

        print("Configuring sequencer...")
        # Setup the pulse picker for single shots in flip flop mode
        pp.flipflop(wait=True)
        # Setup sequencer for requested rate
        sync_mark = int(self._sync_markers[10])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(0) # Run once
        # Setup sequence
        self._seq.rate = 10 
        s = self._seq.dualDuringSequence()
        seq.sequence.put_seq(s)

        print("Now run 'daq.begin_infinite()' and press 'start' on the",
              "sequencer.")
        #yield from count([daq, seq], num=1)

        #if end_run:
        #    time.sleep(3)
        #    daq.end_run()

        #print("Opening shutters...")
        #for shutter in self.shutters:
        #    self._shutters[shutter].open()
