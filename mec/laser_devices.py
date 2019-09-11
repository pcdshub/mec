from ophyd import (Device, EpicsSignal, EpicsSignalRO, Component as C,
                   FormattedComponent as FC)
import time
from mec.db import wp_ab, wp_ef, wp_gh, wp_ij

class Highland(Device):
    """Class for the MEC Highland pulse shaper."""

    # Epics Signals
    pulse_heights = C(EpicsSignal, ':PulseHeights')
    pulse_heights_rbv = C(EpicsSignalRO, ':PulseHeights_RBV')
    fiducial_delay_rbv = C(EpicsSignalRO, ':FiducialDelay_RBV')
    fiducial_height_rbv = C(EpicsSignalRO, ':FiducialHeight_RBV')

    def write_pulse(self, pulse):
        """Write list of pulse heights to Highland."""
        self.pulse_heights.put(pulse)

    @property
    def pulse_rbv(self):
        """Returns list of current pulse heights."""
        heights = self.pulse_heights_rbv.get()
        return heights

    @property
    def fiducial_delay(self):
        """Return current fiducial delay."""
        delay = self.fiducial_delay_rbv.get()
        return delay

    @property
    def fiducial_height(self):
        """Return current fiducial height."""
        height = self.fiducial_height_rbv.get()
        return height

class PolyScienceChiller(Device):
    """Class for the MEC Polyscience chillers."""

    # Epics Signals
    presure_psi = C(EpicsSignalRO, ':PressurePSI')
    presure_kpa = C(EpicsSignalRO, ':PressureKPA')
    temp_setpoint = C(EpicsSignal, ':TempSetpoint')
    temp_rbv = C(EpicsSignalRO, ':CurrentTemp')
    on_off = C(EpicsSignal, ':TurnOnOff')
    run_status = C(EpicsSignalRO, ':RunStatus')
    fault_code = C(EpicsSignalRO, ':FaultStatusCode')
    fault_status = C(EpicsSignalRO, ':FaultStatus')
        
    def set_temp(self, temp):
        """Set temperature setpoint (in Celsius)."""
        self.temp_setpoint.put(temp)

    def turn_on(self):
        """Turn on the chiller."""
        self.on_off.put(1)

    def turn_off(self):
        """Turn off the chiller."""
        self.on_off.put(0)

    @property
    def temp(self):
        """Readback the current temperature (in Celsius)."""
        curr_temp = self.temp_rbv.get()
        return curr_temp

    @property
    def status(self):
        """Readback the run status."""
        stat = self.run_status.get()
        return stat
   
    @property
    def pressure_psi(self):
        """Readback of the pressure in PSI."""
        psi = self.pressure_psi.get()
        return psi

    @property
    def pressure_kpa(self):
        """Readback of the pressure in KPA."""
        kpa = self.pressure_kpa.get()
        return kpa

    @property
    def fault_status(self):
        """Readback of the current fault status string."""
        string = self.fault_status.get()
        return string

    @property
    def fault_code(self):
        """Readback of the current fault code."""
        code = self.fault_code.get()
        return code


#class TDKLambda(Device):
#    """Class for the MEC TDKLambda power supplies."""
#
#    # Epics signals
#    enable = C(EpicsSignal, ':EnableOutput') 
#    enable_rbv = C(EpicsSignalRO, ':EnableOutput_RBV')
#    voltage_setpoint = C(EpicsSignal, ':VoltageSetPoint') 
#    voltage_rbv = C(EpicsSignalRO, ':ActualVoltage')
#    current_setpoint = C(EpicsSignal, ':CurrentSetPoint') 
#    current_rbv = C(EpicsSignalRO, ':ActualCurrent')
#    reset = C(EpicsSignal, ':ResetTDK')
#
#    def enable(self):
#        """Enable the output of the TDK Lambda power supply."""
#        self.enable.put(1)
#    
#    def disable(self):
#        """Disable the output of the TDK Lambda power supply."""
#        self.enable.put(0)
#
#    def set_voltage(self, voltage):
#        """Change the voltage setpoint of the power supply."""
#        self.voltage_setpoint.put(voltage)
#
#    def set_current(self, current):
#        """Change the current setpoint of the power supply."""
#        self.current_setpoint.put(current)
#
#    def reset(self):
#        """Reset the power supply and place it in a safe condition."""
#        self.reset.put(1)
#
#    @property
#    def voltage(self):
#        """Readback the current voltage output of the power supply."""
#        volt = self.voltage_rbv.get()
#        return volt
#
#    @property
#    def current(self):
#        """Readback of the current output of the power supply."""
#        curr = self.current_rbv.get()
#        return curr
#
#    @property
#    def enabled(self):
#        """Readback of the enable state of the power supply. True if enabled, 
#        false otherwise."""
#        state = self.enable_rbv.get()
#        if state == 1:
#            return True
#        elif state == 0:
#            return False
#        else:
#            print("Unknown enable state.")
#
#class EDrive(Device):
#    """Class for the MEC EDrive power supply."""
#
#    # Epics Signals
#    emission = C(EpicsSignal, ":Emission")
#    emission_rbv = C(EpicsSignalRO, ":Emission_RBV")
#    pulsewidth = C(EpicsSignal, ":PulseWidth")
#    pulsewidth_rbv = C(EpicsSignalRO, ":PulseWidth_RBV")
#    current = C(EpicsSignal, ":ActiveCurrent")
#    current_rbv = C(EpicsSignalRO, ":SensedCurrent")
#    voltage_rbv = C(EpicsSignalRO, ":PowerSupply")
#    temp_rbv = C(EpicsSignalRO, ":Temperature")
#    fault_status = C(EpicsSignalRO, ":FaultState")
#
#    def enable(self):
#        """Enable the emission of the Edrive."""
#        self.emission.put(1)
#
#    def disable(self):
#        """Disable the emission of the Edrive."""
#        self.emission.put(0)
#
#    def set_pulsewidth(self, width):
#        """Set the pulsewidth of the Edrive."""
#        self.pulsewidth.put(width)
#
#    def set_current(self, current):
#        """Set the current output of the Edrive."""
#        self.current.put(current)
#
#    @property
#    def enabled(self):
#        """Check the emission state of the Edrive. True if emission is on,
#        False otherwise."""
#        state = self.emission_rbv.get()
#        return state
#
#    @property
#    def pulsewidth(self):
#        """Get the current pulsewidth of the Edrive."""
#        width = self.pulsewidth_rbv.get()
#        return width
#
#    @property
#    def current(self):
#        """Get the current output of the Edrive."""
#        curr = self.current_rbv.get()
#        return curr
#        
#    @property
#    def voltage(self):
#        """Get the voltage output of the Edrive."""
#        volt = self.voltage_rbv.get()
#        return volt
#
#    @property
#    def temperature(self):
#        """Get the temperature of the Edrive."""
#        temp = self.temp_rbv.get()
#        return temp
#
#    @property
#    def fault_status(self):
#        """Get the fault status of the Edrive."""
#        fault = self.fault_status.get()
#        return fault
#
#class IXBlueBiasGenerator(Device):
#    """Class for MEC IX Blue laser bias controller."""
#    
#    # Epics signals
#    bias = C(EpicsSignal, ":BiasValue")
#    bias_rbv = C(EpicsSignalRO, ":BiasValue_RBV")
#    run_mode = C(EpicsSignal, ":RunningMode")
#    run_mode_rbv = C(EpicsSignalRO, ":RunningMode_RBV")
#    scan_restart = C(EpicsSignal, ":ScanRestart")
#    auto_calibration = C(EpicsSignal, ":AutoCalibration")
#    comm_enable = C(EpicsSignal, ":COMM:ENABLE")
#    error_status = C(EpicsSignalRO, ":ErrorStatus")
#
#    def set_bias(self, bias):
#        """Set the bias value of the bias controller (in mV)."""
#        self.bias.put(bias)
#
#    def set_mode(self, mode):
#        """Set the run mode of the bias controller (AUTO or MAN)."""
#        self.run_mode.put(mode)
#
#    def restart_scan(self):
#        """Restart the bias scan."""
#        self.scan_restart.put(1)
#
#    def set_calibration(self, cal):
#        """Set the calibration mode. Can be QUAD, MIN, or MAX."""
#        self.auto_calibration.put(cal)
#
#    def enable_com(self):
#        """Enable remote communication."""
#        self.comm_enable.put(1)
#
#    def disable_com(self):
#        """Disable remote communication."""
#        self.comm_enable.put(0)
#
#    @property
#    def bias(self):
#        """Return the current bias in mV."""
#        volt = self.bias_rbv.get()
#        return volt
#
#    @property
#    def run_mode(self):
#        """Return the run mode of the bias controller."""
#        mode = self.run_mode_rbv.get()
#        return mode
#
#    @property
#    def error_status(self):
#        """Return the error status of the bias controller."""
#        error = self.error_status.get()
#        return error
#
#

class PU610K_Channel(Device):
    """Class for the MEC PU610K PFN charging system channels."""

    _enabled = C(EpicsSignalRO, ':ENABLE_RBV')
    _enable  = C(EpicsSignal,   ':ENABLE')
    _desc    = C(EpicsSignalRO, ':NAME')
    _vset    = C(EpicsSignal,   ':VOLTAGE')
    _vget    = C(EpicsSignalRO, ':VOLTAGE_MEASURED')
    _inh     = C(EpicsSignal,   ':CHARGE_INHIBIT')
    _inh_RBV = C(EpicsSignalRO, ':CHARGE_INHIBIT_RBV')
    _cntdown = C(EpicsSignal,   ':CI_COUNTDOWN')
    _state   = C(EpicsSignalRO, ':CHARGE_STATE')
    _status  = C(EpicsSignalRO, ':ERRORMSG')

    @property
    def enabled(self):
        rbv = self._enabled.get()
        if rbv == 'Enabled':
            return True
        else:
            return False

    def enable(self):
        self._enable.put(1)

    def disable(self):
        self._enable.put(0)

    @property
    def chan_name(self):
        return self._desc.get()

    @property
    def voltage(self):
        return self._vget.get()

    @voltage.setter
    def voltage(self, value):
        self._vset.put(value)

    @property
    def charge_inhibit(self):
        return self._inh_RBV.get()

    @charge_inhibit.setter
    def charge_inhibit(self, value):
        self._inh.put(value)
    
    @property
    def countdown(self):
        return self._cntdown.get()

    @countdown.setter
    def countdown(self, value):
        self._countdown.put(value)

    @property
    def state(self):
        state_dict = {0: 'Not Charging',
                      1: 'Charging',
                      2: 'Charged'}
        return state_dict[self._state.get()]

    @property
    def status(self):
        return self._status.get()
 
class PU610K(Device):
    """Class for the MEC PFN charging racks."""
    _charge = C(EpicsSignal, ':START_CHARGE')
    _mode = C(EpicsSignal, ':MODE')
    _mode_rbv = C(EpicsSignalRO, ':MODE_RBV')
    _mode_ok = C(EpicsSignalRO, ':MODE_OK')
    _fault = C(EpicsSignal, ':FAULT')
    _charge_ok = C(EpicsSignalRO, ':CHARGE_OK')
    _wp_ab = wp_ab
    _wp_ef = wp_ef
    _wp_gh = wp_gh
    _wp_ij = wp_ij

    __chancd = C(PU610K_Channel, ':CH0')
    __chana =  C(PU610K_Channel, ':CH1')
    __chanb =  C(PU610K_Channel, ':CH2')
    __chane =  C(PU610K_Channel, ':CH3')
    __chanf =  C(PU610K_Channel, ':CH4')
    __chang =  C(PU610K_Channel, ':CH5')
    __chanh =  C(PU610K_Channel, ':CH6')
    __chani =  C(PU610K_Channel, ':CH7')
    __chanj =  C(PU610K_Channel, ':CH8')

    @property
    def charged(self):
        c = self._charge_ok.get()
        if c == 0:
            return False
        elif c == 1:
            return True
        else:
            raise Exception("Unknown PFN charge state: {}".format(c))

    @property
    def faulted(self):
        f = self._fault.get()
        if c == 1:
            return True
        else:
            return False

    @property
    def ready(self):
        mode_rbv = self._mode_rbv.get() 
        mode_ok = self._mode_ok.get()
        if (mode_rbv == 2) and (mode_ok == 0):
            return True
        else:
            return False   

    @property
    def stand_by(self):
        mode_rbv = self._mode_rbv.get() 
        mode_ok = self._mode_ok.get()
        if (mode_rbv == 1) and (mode_ok == 0):
            return True
        else:
            return False 
  
    @property
    def stopped(self):
        mode_rbv = self._mode_rbv.get() 
        mode_ok = self._mode_ok.get()
        if (mode_rbv == 0) and (mode_ok == 0):
            return True
        else:
            return False 
  
    def charge(self):
        """Charge the PFN racks based on current settings."""

        self._mode.put(0) # First go to stop to clear any errors
        while not self.stopped:
            time.sleep(0.1)

        self._mode.put(1) # Now go to standby to start cooling
        while not self.standby:
            time.sleep(0.1)

        self._mode.put(2) # now go to "ready" and wait. Requires at least
                          # a 5 second delay (HW 'feature').  
        while not self.ready:
            time.sleep(0.1)

        self._charge.put(1)
        print("Charging, please wait ...")
        while not self.charged:
            time.sleep(1)
        print("Charging complete!")

    def discharge(self):
        """Discharge the PFN racks."""
        self.mode.put(0)

    def ALL(self):
        self.__chancd.enable()
        self.__chang.enable()
        self.__chanh.enable()
        self.__chani.enable()
        self.__chanj.enable()
        self.__chana.enable()
        self.__chanb.enable()
        self.__chane.enable()
        self.__chanf.enable()
        self._wp_ab.mv_on()
        self._wp_ef.mv_on()
        self._wp_gh.mv_on()
        self._wp_ij.mv_on()

    def ALL_OFF(self):
        self.__chancd.disable()
        self.__chang.disable()
        self.__chanh.disable()
        self.__chani.disable()
        self.__chanj.disable()
        self.__chana.disable()
        self.__chanb.disable()
        self.__chane.disable()
        self.__chanf.disable()
        self._wp_ab.mv_off()
        self._wp_ef.mv_off()
        self._wp_gh.mv_off()
        self._wp_ij.mv_off()

    def GHIJ(self):
        """Enable the GHIJ arms, disable ABEF arms."""
        self.__chancd.enable()
        self.__chang.enable()
        self.__chanh.enable()
        self.__chani.enable()
        self.__chanj.enable()
        self.__chana.disable()
        self.__chanb.disable()
        self.__chane.disable()
        self.__chanf.disable()
        self._wp_ab.mv_off()
        self._wp_ef.mv_off()
        self._wp_gh.mv_on()
        self._wp_ij.mv_on()

    def ABEF(self):
        """Enable the ABEF arms, disable GHIJ arms."""
        self.__chancd.enable()
        self.__chana.enable()
        self.__chanb.enable()
        self.__chane.enable()
        self.__chanf.enable()
        self.__chang.disable()
        self.__chanh.disable()
        self.__chani.disable()
        self.__chanj.disable()
        self._wp_ab.mv_on()
        self._wp_ef.mv_on()
        self._wp_gh.mv_off()
        self._wp_ij.mv_off()
