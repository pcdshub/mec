from ophyd import (Device, EpicsSignal, EpicsSignalRO, Component as C,
                   FormattedComponent as FC)
from pcdsdevices import epics_motor

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

class M824_Axis(Device):
    """Axis subclass for PI_M824_Hexapod class."""
    
    axis = C(EpicsSignal, '')
    axis_rbv = C(EpicsSignal, ':rbv')

    def mv(self, pos):
        """Absolute move to specified position."""
        self.axis.put(pos)
    
    def mvr(self, inc):
        """Move relative distance."""
        curr_pos = self.axis_rbv.get()
        next_pos = curr_pos + inc
        self.axis.put(next_pos)

    def wm(self):
        """Return current axis position (where motor)."""
        curr_pos = self.axis_rbv.get()
        return curr_pos
        
class PI_M824_Hexapod(Device):
    """Class for the main MEC TC hexapod. Model M-824 from PI."""
    # Setup axes
    x = C(M824_Axis, ':Xpr')
    y = C(M824_Axis, ':Ypr')
    z = C(M824_Axis, ':Zpr')
    u = C(M824_Axis, ':Upr')
    v = C(M824_Axis, ':Vpr')
    w = C(M824_Axis, ':Wpr')

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


