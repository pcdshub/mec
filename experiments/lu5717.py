import numpy as np
import time
import logging
from bluesky.plans import scan
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from ophyd import (Device, EpicsSignal, EpicsSignalRO, Component as Cpt)
from mec.db import seq, daq
from mec.db import mec_pulsepicker as pp
from mec.db import tomo_motor, lamo_motor
from mec.db import tgx, tgy, tgz

logger = logging.getLogger(__name__)


class piAxis(Device):
    sens_raw = Cpt(EpicsSignalRO, ':SENSORPOSGET')
    sens_filt = Cpt(EpicsSignalRO, ':SENSORPOSFILT')

    servo_pos_set = Cpt(EpicsSignal, ':SERVOPOSSET')
    servo_pos_get = Cpt(EpicsSignal, ':SERVOPOSGET')

    openloop_pos_set = Cpt(EpicsSignal, ':OPENLOOPPOSSET')
    openloop_pos_get = Cpt(EpicsSignalRO, ':OPENLOOPPOSGET')

    velocity_set = Cpt(EpicsSignal, ':VELOCITYSET')
    velocity_get = Cpt(EpicsSignalRO, ':VELOCITYGET')

    status = Cpt(EpicsSignalRO, ':MOVING')
    servo_mode = Cpt(EpicsSignal, ':SERVOMODESET')

    def mv(self, pos):
        """Move the piezo axis to the specified position. The motion command
        will be closed-loop or open-loop, depending on the current mode of the
        piezo controller."""
        if self.mode == 1:
            self.servo_pos_set.put(pos)
        elif self.mode == 0:
            self.openloop_pos_set.put(pos)
        else:
            raise ValueError("Unrecognized piezo mode {}!".format(self.mode))

    def wm(self):
        """Return the current piezo position. The position returned will be
        closed-loop or open-loop, depending on the current mode of the piezo
        controller."""
        if self.mode == 1:
            return self.servo_pos_get.get()
        elif self.mode == 0:
            return self.openloop_pos_get.get()
        else:
            raise ValueError("Unrecognized piezo mode {}!".format(self.mode))

    @property
    def mode(self):
        """Get the mode of the piezo axis. 0 = Open loop, 1 = closed loop."""
        return self.servo_mode.get()

#    @mode.setter
#    def mode(self, m):
#        """Set the mode of the piezo axis. 0 = Open loop, 1 = closed loop."""
#        self.servo_mode.put(int(m))

    @property
    def velocity(self):
        """Get the current velocity of the piezo axis."""
        v = self.velocity_get.get()
        return v

    @velocity.setter
    def velocity(self, velo):
        """Set the velocity of the piezo axis."""
        self.velocity_set.put(velo)

    @property
    def moving(self):
        """Return the moving status of the piezo axis."""
        moving = self.status.get()
        if moving == 1:
            return True
        else:
            return False


class piHera(Device):
    """Class for the PI Hera piezo controller."""
    ch1 = Cpt(piAxis, ':01')
    ch2 = Cpt(piAxis, ':02')
    ch3 = Cpt(piAxis, ':03')

    x = ch1
    y = ch3
    z = ch2

    def wm(self):
        """Return the positions for each channel of the controller. Gives a
        list of the channel positions: [ch1, ch2, ch3]."""
        c1_pos = self.ch1.wm()
        c2_pos = self.ch2.wm()
        c3_pos = self.ch3.wm()

        return [c1_pos, c2_pos, c3_pos]

    def mv(self, positions):
        """Move the piezo axes to the specified positions. Takes a list of
        three positions, corresponding to ch1, ch2 and ch3, respectively."""
        self.ch1.mv(positions[0])
        self.ch2.mv(positions[1])
        self.ch3.mv(positions[2])

    @property
    def mode(self):
        """Function to return the servo mode of all 3 channels. 0 == Open loop,
        1 == Closed loop."""
        return [self.ch1.mode, self.ch2.mode, self.ch3.mode]

#    @mode.setter
#    def mode(self, mode):
#        """Function to set the servo mode of all 3 channels. 0 == Open loop,
#        1 == Closed loop."""
#        self.ch1.mode(mode)
#        self.ch2.mode(mode)
#        self.ch3.mode(mode)

    @property
    def moving(self):
        """Returns the moving status of the controller. If any axis is
        currently moving, then this return True, else False."""
        if self.ch1.moving or self.ch2.moving or self.ch3.moving:
            return True
        else:
            return False


class User():

    pi = piHera('MEC:MZM', name='PI Hera controller')
    _tomo_motor = tomo_motor  # Tomography motor, defined in questionnaire
    _lamo_motor = lamo_motor  # Laminography motor, defined in questionnaire

    def tomo_scan(self, tomo_start, tomo_end, npoints, ndaq, record=True):
        """Return a tomography scan plan.

        Usage
        -----
        p = x.tomo_scan(tomo_start, tomo_end, npoints, ndaq, record=True)
        RE(p)

        Parameters
        ----------

        tomo_start : float
            Starting position of the tomography scan (in degrees).

        tomo_end : float
            Ending position of the tomography scan (in degrees).

        npoints : int
            Number of points to divide the tomography scan into. Separation
            between scan points is equal to (tomo_end - tomo_start)/num_points.

        ndaq : int
            Number of points to record for each tomography position.

        record: bool
            Whether or not to record in the DAQ. Defaults to True.

        Examples
        --------

        # Use default DAQ settings
        tomo_scan(75.0, 85.0, 10)

        # Record a different number of data points per tomography position
        tomo_scan(75.0, 85.0, 10, ndaq=1500)

        # Don't record
        tomo_scan(75.0, 85.0, 10, record=False)
        """
        # Log stuff
        m = "Returning a tomography scan with the following parameters:"
        logging.debug(m)
        logging.debug("motor: %s", self._tomo_motor)
        logging.debug("tomo_start: %s", tomo_start)
        logging.debug("tomo_end: %s", tomo_end)
        logging.debug("npoints: %s", npoints)
        logging.debug("record: %s", record)

        # Return the plan
        return self.__1DScan(self._tomo_motor, tomo_start, tomo_end, npoints,
                             ndaq, record)

    def lamo_scan(self, lamo_start, lamo_end, npoints, ndaq, record=True):
        """Return a laminography scan plan.

        Usage
        -----
        p = x.lamo_scan(lamo_start, lamo_end, npoints, ndaq, record=True)
        RE(p)

        Parameters
        ----------

        lamo_start : float
            Starting position of the laminography scan (in degrees).

        lamo_end : float
            Ending position of the laminography scan (in degrees).

        npoints : int
            Number of points to divide the laminography scan into. Separation
            between scan points is equal to (lamo_end - lamo_start)/num_points.

        ndaq : int
            Number of points to record for each laminography position.

        record: bool
            Whether or not to record in the DAQ. Defaults to True.

        Examples
        --------

        # Use default DAQ settings
        x.lamo_scan(75.0, 85.0, 10)

        # Record a different number of data points per laminography position
        x.lamo_scan(75.0, 85.0, 10, ndaq=1500)

        # Don't record
        x.lamo_scan(75.0, 85.0, 10, record=False)
        """
        # Log stuff
        m = "Returning laminography scan with the following parameters:"
        logging.debug(m)
        logging.debug("motor: %s", self._lamo_motor)
        logging.debug("lamo_start: %s", lamo_start)
        logging.debug("lamo_end: %s", lamo_end)
        logging.debug("npoints: %s", npoints)
        logging.debug("record: %s", record)

        # Return the plan
        return self.__1DScan(self._lamo_motor, lamo_start, lamo_end, npoints,
                             ndaq, record)

    def __1DScan(self, motor, start, end, npoints, ndaq, record):
        # Setup the event sequencer for the scan
        logging.debug("Setting up the sequencer for %s daq points", ndaq)
        self.__setup_sequencer(ndaq)

        # Setup the pulse picker
        if pp.mode.get() == 3:
            logging.debug("The pulse picker is already in burst mode")
        else:
            logging.debug("Setting up the pulse picker for burst mode")
            pp.burst(wait=True)

        # Setup the DAQ
        daq.record = record
        daq.configure(events=ndaq)
        bps.configure(daq, events=ndaq)  # For plan introspection

        # Add sequencer, DAQ to detectors for scan
        dets = [daq, seq]

        # Log stuff
        logging.debug("Returning __1DScan with the following parameters:")
        logging.debug("motor: {}".format(motor))
        logging.debug("start: {}".format(start))
        logging.debug("end: {}".format(end))
        logging.debug("npoints: {}".format(npoints))
        logging.debug("ndaq: {}".format(ndaq))
        logging.debug("record: {}".format(record))
        logging.debug("detectors: {}".format(dets))

        # Return the plan
        scan_plan = scan(dets,
                         motor, start, end,
                         npoints)

        final_plan = bpp.finalize_wrapper(scan_plan, self.__cleanup_plan())

        return final_plan

    def lamo_grid_scan(self, x_start, x_end, xsteps,
                       y_start, y_end, ysteps,
                       angle, ndaq, record=True):
        """Return a laminography grid scan plan.

        Usage
        -----
        p = x.lamo_grid_scan(x_start, x_end, xsteps, y_start, y_end, ysteps,
                        angle, ndaq, record=True)
        RE(p)

        Parameters
        ----------

        x_start : float
            Starting position of the target x stage (in mm).

        x_end : float
            Ending position of the target x stage (in mm).

        xsteps : int
            Number of steps to divide the x distance into.

        y_start : float
            Starting position of the target y stage (in mm).

        y_end : float
            Ending position of the target y stage (in mm).

        ysteps : int
            Number of steps to divide the y distance into.

        angle : float
            The angle of the laminography stage holder.

        ndaq : int
            Number of points to record for each laminography position.

        record: bool
            Whether or not to record in the DAQ. Defaults to True.

        Examples
        --------

        # Record 1000 points per scan
        x.lamo_grid_scan(14.853, 14.903, 10, 6.690, 6.740, 10,
                        45, ndaq=1000, record=True)

        # Record a different number of data points per laminography position
        x.lamo_grid_scan(14.853, 14.903, 10, 6.690, 6.740, 10,
                        45, ndaq=1500, record=True)

        # Don't record
        x.lamo_grid_scan(14.853, 14.903, 10, 6.690, 6.740, 10,
                        45, ndaq=1500, record=False)
        """

        grid_plan = self.__grid_scan(tgx, x_start, x_end, xsteps,
                                     tgy, y_start, y_end, ysteps,
                                     tgz, angle, ndaq, record)

        final_plan = bpp.finalize_wrapper(grid_plan, self.__cleanup_plan())

        return final_plan

    def __grid_scan(self, x_motor, x_start, x_end, xsteps,
                    y_motor, y_start, y_end, ysteps,
                    z_motor, angle, ndaq, record=True):
        logging.debug("Setting up the sequencer for %s daq points", ndaq)
        self.__setup_sequencer(ndaq)

        # Setup the pulse picker
        if pp.mode.get() == 3:
            logging.debug("The pulse picker is already in burst mode")
        else:
            logging.debug("Setting up the pulse picker for burst mode")
            pp.burst(wait=True)

        # Setup the DAQ
        daq.record = record
        daq.configure(events=ndaq)
        bps.configure(daq, events=ndaq)  # For plan introspection

        # Add sequencer, DAQ to detectors for scan
        dets = [daq, seq]

        # Log stuff
        logging.debug("Returning __grid_scan with the following parameters:")
        logging.debug("x_start: {}".format(x_start))
        logging.debug("x_end: {}".format(x_end))
        logging.debug("xsteps: {}".format(xsteps))
        logging.debug("y_start: {}".format(y_start))
        logging.debug("y_end: {}".format(y_end))
        logging.debug("y_steps: {}".format(ysteps))
        logging.debug("angle: {}".format(angle))
        logging.debug("ndaq: {}".format(ndaq))
        logging.debug("record: {}".format(record))
        logging.debug("detectors: {}".format(dets))

        z_start = z_motor.wm()

        x_step_size = (x_end-x_start)/(xsteps-1)
        logging.debug("X step size: {}".format(x_step_size))
        y_step_size = (y_end-y_start)/(ysteps-1)
        logging.debug("Y step size: {}".format(y_step_size))
        z_step = self.__comp_z(y_step_size, angle)
        logging.debug("Z step size: {}".format(z_step))
        for i in range(ysteps):
            new_y = y_start+y_step_size*i
            logging.debug("Moving Y to {}".format(new_y))
            yield from bps.mv(y_motor, new_y)
            if i != 0:  # Skip first step; assume focus is fine there
                logging.debug("Moving Z by {}".format(z_step))
                yield from bps.mvr(z_motor, z_step)
            yield from scan(dets, x_motor, x_start, x_end, xsteps)

        # Return to original positions
        yield from bps.mv(x_motor, x_start)
        yield from bps.mv(y_motor, y_start)
        yield from bps.mv(z_motor, z_start)

    def __comp_z(self, delta_y, angle):
        """Calculate the amount to compensate in Z direction for motion in the
        Y-axis during a grid scan."""
        comp = delta_y * np.tan(np.pi * angle / 180.)

        return comp

    def __setup_sequencer(self, num_points):
        # Do smart stuff with the sequencer now

        # Setup dummy sequence (stupid hack for weird sequencer behavior)
        dummy_sequence = [[0, 0, 0, 0] for i in range(10)]
        d_sequence = [arr for arr in zip(*dummy_sequence)]
        seq.sequence.put_seq(d_sequence)
        time.sleep(2)

        # PP Open line
        pp_open = [[168, 0, 0, 0]]  # Open pulse picker, no delay

        # Scan trigger
        pi_line = [[170, 2, 0, 0]]  # Give PP 2 beam delays to open

        # Add most of the daq triggers
        daq_lines = [[169, 1, 0, 0] for i in range(num_points-1)]

        # PP Close line
        pp_close = [[168, 0, 0, 0]]  # Close pulse picker, no delay

        # Add last DAQ event
        last_daq = [[169, 1, 0, 0]]

        s = pp_open + pi_line + daq_lines + pp_close + last_daq

        sequence = [arr for arr in zip(*s)]

        seq.sequence.put_seq(sequence)

    def __cleanup_plan(self):
        # Plan to do some cleanup at the end of a scan
        yield from bps.abs_set(pp.cmd_reset, 1)  # Reset pulse picker
        yield from bps.abs_set(pp.cmd_close, 1)  # Close pulse picker
