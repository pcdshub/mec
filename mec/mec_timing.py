from ophyd.signal import EpicsSignal, EpicsSignalRO


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

       
def lpl_save_master_timing():
    _bkup = [\
        TimingChannel('MEC:LAS:DDG:03:aDelayAO', 'MEC:NOTE:DOUBLE:45', 'bkupA'),
        TimingChannel('MEC:LAS:DDG:03:cDelayAO', 'MEC:NOTE:DOUBLE:46', 'bkupC'),
        TimingChannel('MEC:LAS:DDG:03:eDelayAO', 'MEC:NOTE:DOUBLE:47', 'bkupE'),
        TimingChannel('MEC:LAS:DDG:03:gDelayAO', 'MEC:NOTE:DOUBLE:48', 'bkupG')]

    for channel in _bkup:
        channel.save_t0()
