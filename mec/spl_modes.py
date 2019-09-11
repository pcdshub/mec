from ophyd import (Device, EpicsSignal, EpicsSignalRO, Component as C,
                   FormattedComponent as FC)

class DG645(Device):
    """Barebones class for managing DG645 for MEC Uniblitz deployment."""
    
    # EPICS Signals
    ch_AB_pol = C(EpicsSignal, ':abOutputPolarityBO.VAL')
    ch_CD_pol = C(EpicsSignal, ':cdOutputPolarityBO.VAL')

class UniblitzEVRCH(Device):
    """Barebones class for managing EVR channels for MEC Uniblitz deployment."""
    
    # EPICS Signals
    ch_enable = C(EpicsSignal, ':TCTL')
    ch_eventc = C(EpicsSignal, ':TEC')
