# Bob Nagler, (c) Feb 2013
# Hacked to be Ophyd-compatable, Mike Browne, May 2020
# All units are SI

from ophyd import (Device, EpicsSignal, EpicsSignalRO, Component as C,
                   FormattedComponent as FC)
from numpy import *

class VisarBed(Device):
    """ Class that defines a visar bed.

        Calculates VPF, translation distances, etalons, etc.
        All SI units, except in the status where they are printed with units.
        usage: bed1=VISAR(etalon_thickness) ; see __init__ for more options.
        functions: bed1.d() : returns correct translation distance, in m
                   bed1.delay() : returs delay between arm, in s
                   bed1.vfp0() : returns velocity per finge, in m/s
                   bed1.stage_pos(): returns the correct stage position for the etalon used
                   bed1.status() : prints the status; distances in mm, wavelength in nm, other in SI
                   
    
    """
    # Epics Signals
    etalon_h = C(EpicsSignal,    '_ETALON_H')
    z_t0     = C(EpicsSignal,    '_Z_T0')

    def __init__(self, prefix, *args, **kwargs):
        super().__init__(prefix, *args, **kwargs)
        self._landa    = 532e-9
        self._n        = 1.46071
        self._delta    = 0.0318
        self._theta    = 11.31 / 180.0 * pi  # Radians
        self._c       = 299792458 # m/s

    def __call__(self):
        self.status()

    def d(self):
        """ Returns the translation of the visar bed that matches the etalon thickness h."""
        d0=self.etalon_h.get()*(1-1/self._n)
        angle_correction=1.0/(cos(arcsin(sin(self._theta/2.0)/self._n))) #Correction factor: non-normal incidence
        return d0*angle_correction

    def delay(self):
        """ Returns the temporal delay between the two arms of the interferometer."""
        t0=2*self.etalon_h.get()*(self._n-1/self._n)/self._c
        angle_correction=1.0/(cos(arcsin(sin(self._theta/2.0)/self._n))) #Correction factor: non-normal incidence
        return t0*angle_correction

    def vpf0(self):
        """Returns the Velocity Per Fringe of the visar. Uncorrected for windows or fast lens"""
        tau=self.delay()
        return self._landa/(2*tau*(1+self._delta))

    def stage_pos(self):
        """Returns the correct position of the visar stage, for the etalon used."""
        if self.z_t0.get()==None: return None
        else: return self.z_t0.get()+self.d()

    def status(self):
        """Prints out an overview of the VISAR bed."""
        transdis_mm=self.d()*1000.0
        etalon_mm=self.etalon_h.get()*1000.0
        if self.z_t0.get()!=None:
            stage_pos_mm=self.stage_pos()*1000.0
            wl_mm=self.z_t0.get()*1000.0
        else:
            stage_pos_mm=None
            wl_mm=None
        laserwavelength_nm=self._landa*1e9
        
        statstr= "laser wavelength : %.3f nm\n" %laserwavelength_nm
        if wl_mm!=None:statstr+= "White light stage reading : %.3f mm\n" %wl_mm
        statstr+="Etalon thickness : %.3f mm\n" %etalon_mm
        statstr+="Etalon material : n="+str(self._n)+" , delta="+str(self._delta)+"\n"
        statstr+="Correct translation distance : %.3f mm\n" %transdis_mm
        if stage_pos_mm!=None: statstr+="Correct stage position : %.3f mm\n" %stage_pos_mm
        statstr+="Velocity Per Fringe : "+str(self.vpf0())+" m/s\n"
        print(statstr)

    def calc_h(self,vpf):
        """Calculates the etalon distance required for the passed velocity per fringe"""

        tau_req=self._landa/(2*vpf*(1+self._delta))
        angle_correction=cos(arcsin(sin(self._theta/2.0)/self._n))
        h_req=tau_req*self._c*angle_correction/(2*(self._n-1/self._n))
        return h_req
