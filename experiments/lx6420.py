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

from dev.pulseshaping.mecps.mecps import *

from pcdsdevices.targets import XYTargetGrid

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

    tx_motor = target.x
    ty_motor = target.y

    grid = XYTargetGrid(x=tx_motor, y=ty_motor, x_init=0.0, y_init=0.0,
                        x_spacing=-0.363, y_spacing=0.363, x_comp=0.01, y_comp=0.01,
                        name='lv25_targetgrid')


    def x_scan(self, nshots=1, record=True, xrays=False, carriage_return=False):
        """
        Returns a BlueSky plan to perform a scan in X. Collects a 
        number of short pulse laser shots while moving from target to target. 
        
        Parameters:
        -----------
        nshots : int <default: 1>
            The number of shots that you would like to take in the run.

        record : bool <default: True>
            Flag to record the data (or not).

        xrays : bool <default: False>
            Flag to do an optical or x-ray shot. If False, does an optical only
            shot. If True, you do a optical + x-ray shot.

        carriage_return : bool <default: False>
            Flag to return to initial position. 
        """
        logging.debug("Calling User.x_scan with parameters:")        
        logging.debug("nshots: {}".format(nshots))        
        logging.debug("record: {}".format(record))        
        logging.debug("xrays: {}".format(xrays))        

        print("Configuring DAQ...")
        daq.configure(events=0, record=record, begin_sleep=0.1) # run infinitely
#        daq.configure(events=nshots, record=record)
#        daq.begin_infinite()
        
        print("Configuring sequencer...")
        # Setup the pulse picker for single shots in flip flop mode
        pp.flipflop(wait=True)
        # Setup sequencer for requested rate
        sync_mark = int(self._sync_markers[5])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(0) # Run once
        # Setup sequence
        self._seq.rate = 5
        if xrays:
            s = self._seq.duringSequence(1, 'shortpulse')
        else:
            s = self._seq.opticalSequence(1, 'shortpulse')
        seq.sequence.put_seq(s)

        self._shutters[6].close()
        time.sleep(5)

        # Get starting positions
        start = self.grid.wm()
        yield from scan([daq, seq], self.grid.x, start['x'], 
                        (start['x']+self.grid.x_spacing*(nshots-1)), num=nshots)

#        for i in range(nshots):
#            if i is not 0:
#                yield from bps.mv(start['x']+self.grid.x_spacing*i)
##            yield from bps.trigger_and_read([daq,seq])
##            yield from bps.trigger(seq, wait=True)
#            yield from count([daq,seq], num=1)


        if carriage_return:
            # Return to start
            print("Returning to starting position")
            yield from bps.mv(self.grid.x, start['x'])
            yield from bps.mv(self.grid.y, start['y'])

        daq.end_run()

        self._shutters[6].open()


    def _x_position(self, xstart, xspacing, ix, iy, dxx=0.0, dxy=0.0):
        """
        Determine the appropriate X position of a motor on a grid, given
        regular, measured deviations from the ideal grid due to mounting, etc.
        If deviations are omitted, then this will simply return the ideal grid
        position given the defined spacing.

        Parameters
        ----------
        xstart : float
            Initial x position (e.g. x position of target "zero").

        xspacing : float
            Ideal spacing for grid.

        ix : int
            Zero-indexed target x-index. 

        iy : int
            Zero-indexed target y-index.

        dxx : float (default=0.0)
            Deviation in x position per x-index from ideal. 

        dxy : float (deafult=0.0)
            Deviation in x position per y-index from ideal.
        """
        return xstart + (xspacing+dxx)*ix + dxy*iy


    def _y_position(self, ystart, yspacing, ix, iy, dyy=0.0, dyx=0.0):
        """
        Determine the appropriate Y position of a motor on a grid, given
        regular, measured deviations from the ideal grid due to mounting, etc.
        If deviations are omitted, then this will simply return the ideal grid
        position given the defined spacing.

        Parameters
        ----------
        ystart : float
            Initial y position (e.g. y position of target "zero").

        yspacing : float
            Ideal spacing for grid.

        ix : int
            Zero-indexed target x-index. 

        iy : int
            Zero-indexed target y-index.

        dyy : float (default=0.0)
            Deviation in y position per y-index from ideal. 

        dyx : float (deafult=0.0)
            Deviation in y position per x-index from ideal.
        """
        return ystart + (yspacing+dyy)*iy + dyx*ix


    def _list_scan_positions(self, xstart, xspacing, ystart, yspacing, nx, ny, 
                             dxx=0.0, dxy=0.0, dyy=0.0, dyx=0.0):
        """
        Return lists of x and y positions for use in a BlueSky list_scan plan.
        Calculates x and y positions for a sample grid given any non-idealities
        in the grid alignment. 

        Parameters
        ----------
        xstart : float
            Initial x position (e.g. x position of target "zero").

        xspacing : float
            Ideal spacing for grid.

        ystart : float
            Initial y position (e.g. y position of target "zero").

        yspacing : float
            Ideal spacing for grid.

        nx : int
            The number of x positions in the grid.

        ny : int
            The number of y positions in the grid. 

        dxx : float (default=0.0)
            Deviation in x position per x-index from ideal. 

        dxy : float (deafult=0.0)
            Deviation in x position per y-index from ideal.

        dyy : float (default=0.0)
            Deviation in y position per y-index from ideal. 

        dyx : float (deafult=0.0)
            Deviation in y position per x-index from ideal.
        """
        xl = []
        yl = []
        for i in range(ny):
            for j in range(nx):
                xl.append(self._x_position(xstart, xspacing, j, i,  dxx=dxx,
                          dxy=dxy))
                yl.append(self._y_position(ystart, yspacing, j, i, dyy=dyy, 
                          dyx=dyx))

        return xl, yl


    def xy_scan(self, nxshots=1, nyshots=1, record=True, xrays=False,
                carriage_return=False):
        """
        Returns a BlueSky plan to perform a scan in X and Y. Collects a 
        number of short pulse laser shots while moving from target to target. 
        
        Parameters:
        -----------
        nxshots : int <default: 1>
            The number of shots that you would like to take on the x axis for
            each "line" on the target stage.

        nyshots : int <default: 1>
            The number of lines that you want to move on the y axis.

        record : bool <default: True>
            Flag to record the data (or not).

        xrays : bool <default: False>
            Flag to do an optical or x-ray shot. If false, does an optical only
            shot. If true, you do a optical + x-ray shot.

        carriage_return : bool <default: False>
            Flag to return to initial position. 
        """
        logging.debug("Calling User.xy_scan with parameters:")        
        logging.debug("nxshots: {}".format(nxshots))        
        logging.debug("nyshots: {}".format(nyshots))        
        logging.debug("record: {}".format(record))        
        logging.debug("xrays: {}".format(xrays))        

        print("Configuring DAQ...")
        daq.configure(events=0, record=record) # run infinitely
#        daq.begin_infinite()

        print("Configuring sequencer...")
        # Setup the pulse picker for single shots in flip flop mode
        pp.flipflop(wait=True)
        # Setup sequencer for requested rate
        sync_mark = int(self._sync_markers[5])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(0) # Run once
        # Setup sequence
        self._seq.rate = 5
        if xrays:
            s = self._seq.duringSequence(1, 'shortpulse')
        else:
            s = self._seq.opticalSequence(1, 'shortpulse')
        seq.sequence.put_seq(s)

        # Get starting positions
        start = self.grid.wm()

        # Get lists of scan positions
        xl, yl = self._list_scan_positions(start['x'], self.grid.x_spacing,
                                           start['y'], self.grid.y_spacing,
                                           nxshots, nyshots, dxx=0.0,
                                           dxy=self.grid.x_comp, dyy=0.0,
                                           dyx=self.grid.y_comp)

        # Close shutter 6 (requested)
        self._shutters[6].close()
        time.sleep(5)

        # Scan the thing
        def inner():
            yield from list_scan([daq, seq], self.grid.y, yl, self.grid.x, xl)

        yield from inner()

        if carriage_return:
            # Return to start
            print("Returning to starting position")
            yield from bps.mv(self.grid.x, start['x'])
            yield from bps.mv(self.grid.y, start['y'])

        daq.end_run()

        self._shutters[6].open()


    def xy_fly_scan(self, nshots, nrows=2, y_distance=None, rate=5,
                    record=True, xrays=True):
        """
        Plan for doing a 2D fly scan. Uses the target x motor as the flying
        axis, running for a specified distance at a specified velocity, taking
        shots at a specified rate. 

        Parameters
        ----------
        nshots : int
            The number of shots to take in the x scan. 

        rate : int <default : 5>
            The rate at which to take shots (120, 30, 10, 5, 1)

        y_distance : float <default : x.grid.y_spacing>
            The distance to move the y stage down. 

        nrows : int <default : 2>
            The number of "rows" to scan the x stage on.

        record : bool <default : True>
            Flag to record the data. 

        xrays : bool <default : True>
            Flag to take an x-ray + optical (True) shot or optical only (False).
        """
        logging.debug("rate: {}".format(rate))
        logging.debug("nshots: {}".format(nshots))
        logging.debug("nrows: {}".format(nrows))
        logging.debug("record: {}".format(record))
        logging.debug("xrays: {}".format(xrays))

        if not y_distance:
            y_distance = self.grid.y_spacing
        logging.debug("y_distance: {}".format(y_distance))

        assert rate in [120, 30, 10, 5, 1], "Please choose a rate in {120, 30, 10,5,1}"

        print("Configuring DAQ...")
        daq.configure(events=0, record=record) # run infinitely
        daq.begin_infinite()

        print("Configuring sequencer...")
        # Setup the pulse picker for single shots in flip flop mode
        pp.flipflop(wait=True)
        # Setup sequencer for requested rate
        sync_mark = int(self._sync_markers[rate])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(1) # Run for n shots
        seq.rep_count.put(nshots)
        # Setup sequence
        self._seq.rate = rate
        if xrays:
            s = self._seq.duringSequence(1, 'shortpulse')
        else:
            s = self._seq.opticalSequence(1, 'shortpulse')
        seq.sequence.put_seq(s)

        # Get starting positions
        start = self.grid.wm()

        # Calculate and set velocity
        vel = self.grid.x_spacing * rate  # mm * (1/s) = mm/s
        self.grid.x.velocity.put(vel)

        # Estimate distance to move given requested shots and rate
        dist = (nshots/rate)*vel  # (shots/(shots/sec))*mm/s = mm

        # Close shutter 6 (requested)
        self._shutters[6].close()
        time.sleep(5)

        for i in range(nrows):
            if i != 0:
                yield from bps.mvr(self.grid.y, y_distance)
            # Play the sequencer
            seq.play_control.put(1) 
            
            # Start the move
            yield from bps.mvr(self.grid.x, dist) # Waits for move to complete

            # Make sure the sequencer stopped
            seq.play_control.put(0) 

            yield from bps.mv(self.grid.x, start['x'])

        # Return to start
        print("Returning to starting position")
        yield from bps.mv(self.grid.x, start['x'])
        yield from bps.mv(self.grid.y, start['y'])

        daq.end_run()

        self._shutters[6].open()

