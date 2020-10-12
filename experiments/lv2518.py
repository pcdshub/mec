import logging
import bluesky.plan_stubs as bps
from bluesky.plans import count, scan, list_scan
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

from pcdsdevices.targets import XYTargetGrid

logger = logging.getLogger(__name__)

tx_motor = target.x
ty_motor = target.y

class User():

    grid = XYTargetGrid(x=tx_motor, y=ty_motor, x_init=0.0, y_init=0.0,
                        x_spacing=0.3, y_spacing=0.3, x_comp=0.01, y_comp=0.01,
                        name='lv25_targetgrid')

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

    def close_shutters(self):
        print("Closing shutters...")
        for shutter in self.shutters:
            self._shutters[shutter].close()

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
        daq.configure(events=0, record=record) # run infinitely
        daq.begin_infinite()
        
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
        yield from scan([daq, seq], self.grid.x, start['x'], 
                        (start['x']+self.grid.x_spacing*(nshots-1)), num=nshots)

        if carriage_return:
            # Return to start
            print("Returning to starting position")
            yield from bps.mv(self.grid.x, start['x'])
            yield from bps.mv(self.grid.y, start['y'])

        daq.end_run()


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
        daq.begin_infinite()

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

#    def _1D_fly_scan(self, motor, start, end, nevents, record, use_l3t,
#                     controls, end_run, carriage_return, predelay, postdelay,
#                     rate):
#
#        """Plan for setting up a one-dimensional fly scan."""
#
#        logging.debug("Generating 1D fly scan shot plan using _1D_fly_scan.")
#        logging.debug("_shot_plan config:")
#        logging.debug("{}".format(self._config))
#        logging.debug("motor: {}".format(motor))
#        logging.debug("start: {}".format(start))
#        logging.debug("end: {}".format(end))
#        logging.debug("predelay: {}".format(predelay))
#        logging.debug("postdelay: {}".format(postdelay))
#        logging.debug("Record: {}".format(record))
#        logging.debug("use_l3t: {}".format(use_l3t))
#        logging.debug("controls: {}".format(controls))
#        logging.debug("carriage_return: {}".format(carriage_return))
#        logging.debug("end_run: {}".format(end_run))
#        logging.debug("rate: {}".format())
#
#        # Adjust start/end for any pre/post-delays
#        if bool(predelay):
#            if (end-start) >= 0:
#                start -= predelay
#            else:
#                start += predelay
#
#        if bool(postdelay):
#            if (end-start) >= 0:
#                end += postdelay
#            else:
#                end -= postdelay
#
#        m_velo = motor.velocity.get()
#        # Total number of events: (mm/(mm/s))*(events/s) = events
#        nevents = int((abs(end-start)/m_velo)*rate)
#
#        # Get into initial position
#        yield from bps.mv(motor, start)
#
#        motor.mv(end)
#        # Shoot stuff
#        yield from self._single_shot_plan(record=record, use_l3t=use_l3t,
#                                          controls=controls, end_run=end_run)
#
#        if carriage_return:
#            yield from bps.mv(motor, start)
#        if end_run:
#            daq.end_run()
#
#    def fly_scan_1D_shot(self, motor, start, end, record=True, use_l3t=False,
#                         controls=[], end_run=True, carriage_return=True,
#                         predelay=None, postdelay=None):
#        """Return a plan for doing a 1D fly scan with the laser, continuously
#        taking shots along the way."""
#        dev = []
#        for shutter in self._config['shutters']:
#            dev.append(self._shutters[shutter])
#
#        @bpp.stage_decorator(dev)
#        @bpp.run_decorator()
#        def inner(motor, start, end, record, use_l3t, controls, end_run,
#                  carriage_return, predelay, postdelay):
#
#            plan = self._1D_fly_scan(motor, start, end, record,
#                                     use_l3t, controls, end_run,
#                                     carriage_return, predelay, postdelay)
#
#            return plan
#
#        return inner(motor, start, end, record, use_l3t, controls, end_run,
#                     carriage_return, predelay, postdelay)
#
#    def _2D_fly_scan_plan(self, motor1, m1_start, m1_end, motor2, m2_start,
#                          m2_end, m2_steps, predelay, postdelay, record,
#                          use_l3t, controls, end_run, carriage_return):
#        # Log stuff
#        logging.debug("Returning _2D_fly_scan with the following parameters:")
#        logging.debug("m1_start: {}".format(m1_start))
#        logging.debug("m1_end: {}".format(m1_end))
#        logging.debug("m2_start: {}".format(m2_start))
#        logging.debug("m2_end: {}".format(m2_end))
#        logging.debug("m2_steps: {}".format(m2_steps))
#        logging.debug("end_run: {}".format(end_run))
#        logging.debug("carriage_return: {}".format(carriage_return))
#
#        m2_step_size = (m2_end-m2_start)/(m2_steps-1)
#        logging.debug("m2 step size: {}".format(m2_step_size))
#        for i in range(m2_steps):
#            new_m2 = m2_start+m2_step_size*i
#            logging.debug("Moving motor2 to {}".format(new_m2))
#            yield from bps.mv(motor2, new_m2)
#            logging.debug("Calling self._1D_fly_scan...")
#            yield from self._1D_fly_scan(motor1, m1_start, m1_end, record,
#                                         use_l3t, controls, False,
#                                         carriage_return, predelay, postdelay)
#            #yield from self._single_shot_plan(record, use_l3t, controls,
#            #                                   False)
#            # Last move in the scan, so check cleanup settings
#            #if j == (m2_steps-1):
#        if carriage_return:
#            yield from bps.mv(motor1, m1_start)
#            yield from bps.mv(motor2, m2_start)
#        if end_run:
#            daq.end_run()
#
#    def fly_scan_2D_shot(self, motor1, m1_start, m1_end, motor2, m2_start,
#                         m2_end, m2_steps, predelay=None, postdelay=None,
#                         record=True, use_l3t=False, controls=[], end_run=True,
#                         carriage_return=True):
#        """Return a plan for doing a 2D fly scan with the laser, continuously
#        taking shots along the way."""
#
#        dev = []
#        for shutter in self._config['shutters']:
#            dev.append(self._shutters[shutter])
#
#        @bpp.stage_decorator(dev)
#        @bpp.run_decorator()
#        def inner(motor1, m1_start, m1_end, motor2, m2_start, m2_end, m2_steps,
#                  predelay, postdelay, record, use_l3t, controls, end_run,
#                  carriage_return):
#
#            plan = self._2D_fly_scan_plan(motor1, m1_start, m1_end, motor2,
#                                          m2_start, m2_end, m2_steps, predelay,
#                                          postdelay, record, use_l3t, controls,
#                                          end_run, carriage_return)
#
#            return plan
#
#        return inner(motor1, m1_start, m1_end, motor2, m2_start, m2_end,
#                     m2_steps, predelay, postdelay, record, use_l3t, controls,
#                     end_run, carriage_return)
#
#
