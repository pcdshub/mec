from ophyd import (Device, EpicsSignal, EpicsSignalRO, Component as C,
                   FormattedComponent as FC)
from pcdsdevices.interface import FltMvInterface
from pcdsdevices.pv_positioner import PVPositionerComparator
from ophyd.epics_motor import EpicsMotor
from ophyd.positioner import PositionerBase
from ophyd.pv_positioner import PVPositioner
from pcdsdevices import epics_motor
import time

class TCShutter(Device):
    """Class for shutters used around the MEC target chamber."""
    # Epics Signals
    control_pv = C(EpicsSignal, '')
    open_value = 0
    closed_value = 1

    # Control functions
    def close(self):
        self.control_pv.put(self.closed_value)

    def open(self):
        self.control_pv.put(self.open_value)

    @property
    def isclosed(self):
        if self.control_pv.get() == self.closed_value:
            return True
        else:
            return False
    
    @property
    def isopen(self):
        if self.control_pv.get() == self.open_value:
            return True
        else:
            return False

    def stage(self):
        print("Closing {}...".format(self.name))
        self.close()
        time.sleep(0.5)

    def unstage(self):
        print("Opening {}...".format(self.name))
        self.open()


class LedLights(Device):
    """LED lights controlled by turning AC PDU channel on/off"""
    # Epics Signals
    control_pv = C(EpicsSignal, ':SetControlAction')
    on_value = 1
    off_value = 2

    # Control functions
    def on(self):
        self.control_pv.put(self.on_value)

    def off(self):
        self.control_pv.put(self.off_value)
    
    @property
    def ison(self):
        if self.control_pv.get() == self.on_value:
            return True
        else:
            return False
    
    @property
    def isoff(self):
        if self.control_pv.get() == self.off_value:
            return True
        else:
            return False

# The PI hexapod status PV is not very reliable, I implemented this as a
# PVPositionerComparator class to get scans to run properly; my first attempt
# using a PVPositioner would just hang using a normal PVPositioner object since 
# done wasn't getting updated properly. This object does have an issue with
# hanging when the position is commanded outside the limits; there are no limit 
# switches to indicate that a limit has been reached. The limits are set in the
# combined hexapod parent class, but currently PVPositioner doesn't do anything
# with the limits, and these limits may need to be modified depending on 
# experiment configuration, since the limits are dependent upon current 
# physical position. 
class M824_Axis(PVPositionerComparator):
    """Axis subclass for PI_M824_Hexapod class."""
    setpoint = C(EpicsSignal, '')
    readback = C(EpicsSignal, ':rbv')
    atol = 0.001 # one micron seems close enough

    def done_comparator(self, readback, setpoint):
        if setpoint-self.atol < readback and readback < setpoint+self.atol:
            return True
        else:
            return False
    
        
class PI_M824_Hexapod(Device):
    """Class for the main MEC TC hexapod. Model M-824 from PI."""

    def __init__(self, prefix, **kwargs):
        # Setup axes
        self.x = M824_Axis(prefix+':Xpr', name='x', limits=(-22.5, 22.5))
        # Hexapod "Z", LUSI "Y"
        self.y = M824_Axis(prefix+':Ypr', name='y', limits=(-12.5, 12.5))
        # Hexapod "Y", LUSI "Z"
        self.z = M824_Axis(prefix+':Zpr', name='z', limits=(-22.5, 22.5))
        self.u = M824_Axis(prefix+':Upr', name='u', limits=(-7.5, 7.5))
        # Hexapod "Z", LUSI "Y"
        self.v = M824_Axis(prefix+':Vpr', name='v', limits=(-12.5, 12.5))
        # Hexapod "Y", LUSI "Z"
        self.w = M824_Axis(prefix+':Wpr', name='w', limits=(-7.5, 7.5))
        super().__init__(prefix, **kwargs)

    # Setup controller level properties
    moving_rbk = C(EpicsSignal, ':moving.RVAL')
    velocity = C(EpicsSignal, ':vel')
    velocity_rbk = C(EpicsSignal, ':vel:rbv')
    error_rbk = C(EpicsSignal, ':error.RVAL')


    # Control functions
    def vel(self, velo):
        """Set velocity, e.g. hexapod.velo(5.0)"""
        self.velocity.put(velo)

    @property
    def vel(self):
        """Returns the current velocity."""
        velocity = self.velocity_rbk.get() 
        return velocity 

    @property
    def moving(self):
        """Returns True if hexapod is moving, False otherwise."""
        moving = self.moving_rbk.get()
        if moving == 1:
            return True
        elif moving == 0:
            return False
        else:
            print("Unknown moving status of %d" % moving)
    
    @property
    def haserror(self):
        """Returns current error status. True if error, False otherwise."""
        error = self.error_rbk.get()
        if error != 0:
            return True 
        else:
            return False


# This should be removed at some point; it has been superceded by a class in
# pcdsdevices. Leaving it in for now.
class TargetStage(Device):
    """Class for MEC target stage. Composite stage consisting of hexapod and
    a linear stage. Linear stage is used for rastering targets in X, while 
    the hexapod is used to move targets in Y and Z (LUSI coordinates).

    Assumes X stage is IMS, Y and Z are hexapod.

    Parameters
    ----------
    xstage: stage object
        Stage used to raster targets in X.
 
    hexapod: hexapod object 
        Base hexapod being used to move targets in Y and Z.

    target_x_space: float
        Spacing in mm between targets in X.

    target_y_space: float
        Spacing in mm between targets in Y.
    ----------
    """
   
    def __init__(self, xstage, hexapod, target_x_space, target_y_space): 
        # Constants.     
        self.x_space = target_x_space
        self.y_space = target_y_space

        # Setup stages.
        self.x = xstage 
        self.y = hexapod.y
        self.z = hexapod.z
        self.hexapod = hexapod
    
    def next(self, num_targets):
        """Move forward (in X) by specified integer number of targets."""
        targets = int(num_targets)
        curr_pos = self.x.wm()
        next_pos = curr_pos + (targets*self.x_space)
        self.x.mv(next_pos)
    
    def back(self, num_targets):
        """Move backward (in X) by specified integer number of targets."""
        targets = int(num_targets)
        curr_pos = self.x.wm()
        next_pos = curr_pos - (targets*self.x_space)
        self.x.mv(next_pos)

    def up(self, num_targets):
        """Move up by specified integer number of targets (stage moves down)."""
        targets = int(num_targets)
        curr_pos = self.y.wm()
        next_pos = curr_pos - (targets*self.y_space)
        self.y.mv(next_pos)

    def down(self, num_targets):
        """Move down by specified integer number of targets (stage moves up)."""
        targets = int(num_targets)
        curr_pos = self.y.wm()
        next_pos = curr_pos + (targets*self.y_space)
        self.y.mv(next_pos)
    
    @property
    def moving(self):
        """Returns True if hexapod or target stage is moving, False otherwise."""
        xmoving = self.x.moving
        hexmoving = self.hexapod.moving
        if hexmoving == True or xmoving == True:
            return True
        elif hexmoving == 0 and xmoving == False:
            return False
        else:
            print("Unknown moving status")


class TargetXYStage(Device):
    """Class for MEC target stage. Composite stage consisting of two linear
    stages. One stage is used for rastering targets in X, while  the other is
    used to move targets in Y (LUSI coordinates).

    Parameters
    ----------
    xstage: stage object
        Stage used to raster targets in X.
 
    ystage: stage object
        Stage used to raster targets in Y.

    target_x_space: float
        Spacing in mm between targets in X.

    target_y_space: float
        Spacing in mm between targets in Y.
    ----------
    """
   
    def __init__(self, xstage, ystage, target_x_space, target_y_space): 
        # Constants.     
        self.x_space = target_x_space
        self.y_space = target_y_space

        # Setup stages.
        self.x = xstage 
        self.y = ystage 
    
    def next(self, num_targets=1):
        """Move forward (in X) by specified integer number of targets."""
        targets = int(num_targets)
        curr_pos = self.x.wm()
        next_pos = curr_pos + (targets*self.x_space)
        self.x.mv(next_pos)
    
    def back(self, num_targets=1):
        """Move backward (in X) by specified integer number of targets."""
        targets = int(num_targets)
        curr_pos = self.x.wm()
        next_pos = curr_pos - (targets*self.x_space)
        self.x.mv(next_pos)

    def up(self, num_targets=1):
        """Move up by specified integer number of targets (stage moves down)."""
        targets = int(num_targets)
        curr_pos = self.y.wm()
        next_pos = curr_pos - (targets*self.y_space)
        self.y.mv(next_pos)

    def down(self, num_targets=1):
        """Move down by specified integer number of targets (stage moves up)."""
        targets = int(num_targets)
        curr_pos = self.y.wm()
        next_pos = curr_pos + (targets*self.y_space)
        self.y.mv(next_pos)
    
    @property
    def moving(self):
        """Returns True if hexapod or target stage is moving, False otherwise."""
        xmoving = self.x.moving
        ymoving = self.y.moving
        if xmoving == True or ymoving == True:
            return True
        else:
            return False
