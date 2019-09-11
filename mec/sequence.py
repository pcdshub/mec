#!/usr/bin/env python
#
# Module for setting up the MEC event sequencer
#

def generateSequence(code_list, total_beamdelta):
    """Generate a sequence given a list of lists containing event codes, and
    the requested beam deltas from the event for that code. 

    Parameters
    ----------
    code_list : list
        list of lists containing beam codes and desired total beam delta from
        the xray event for that code. Example:
        list = [[<eventcode>, <beamdelta>], [<eventcode>, <beamdelta>], ... ]

    total_beamdelta : int
        The number of beam deltas for the sync marker that you are using. For
        example, a sync marker of 5Hz would have 120/5 = 24 beam deltas.
    """
    # Sort codes based on delta from beam event
    sorted_codes = sorted(code_list, key=lambda code: code[1])

    # Generate sequence, assigning beam delta using the beam delta from
    # the next code (the delta of the delta?)
    sorted_seq = []
    for i in range(len(sorted_codes)-1):
        sorted_bd = sorted_codes[i+1][1] - sorted_codes[i][1]
        sorted_seq.append([sorted_codes[i][0], sorted_bd, 0, 0])

    # Deal with any codes that have the same beam delta by making the first
    # code have zero beam delta. This makes them occur (almost) simultaneously.
    for i in range(len(sorted_codes)-1):
        code1_bd = sorted_codes[i][1]
        code2_bd = sorted_codes[i+1][1]

        if code1_bd == code2_bd:
            sorted_codes[i][1] = 0

    # Get the maximum beam delta needed by codes
    max_beamdelta = max([code[1] for code in sorted_codes])

    # Check that the whole sequence will fit in one sync marker
    # TODO: Update function so this isn't a problem? Can that be done?
    if max_beamdelta > total_beamdelta:
        raise Exception("The maximum event code beam delta exceeds the sync "
                        "marker! Please edit your sequence.")

    # Add the last code (furthest away from the event) with the remaining beam
    # delta.
    last_beamdelta = total_beamdelta - max_beamdelta
    sorted_seq.append([sorted_codes[-1][0], last_beamdelta, 0, 0])

    # Reverse the list to give a sequence that is in the same order as it will
    # be applied to the event sequencer
    seq = list(reversed(sorted_seq)) 

    return seq

class Sequence:
    """Class for defining event sequences for the MEC instrument."""
    def __init__(self):
        # MEC event code defs
        self.EC = {'slowcam':      167,
                   'pulsepicker':  168,
                   'daqreadout':   169,
                   'prelaser':     170,
                   'postlaser':    171,
                   'shortpulse':   176,
                   'prelasertrig': 177,
                   'longpulse':    182}

        # Initialize config
        self.prelasertrig = 0
        self.slowcam = False 
        self.slowcamdelay = 5
        self.rate = 5

    @property
    def config(self):
        conf = {'rate': self.rate,
                'prelasertrig': self.prelasertrig,
                'slowcam': self.slowcam,
                'slowcamdelay': self.slowcamdelay}

        return conf

    def configure(self, Rate=5, PreLaserTrig=0, SlowCam=False, SlowCamDelay=5):
        """Configure the sequencer for the given parameters.

        configure(self, Rate=5, PreLaserTrig=0, SlowCam=False, SlowCamDelay=5):

        Parameters
        ----------
        rate : int
            Integer rate at which you want to take laser shots, with or without
            x-rays, synchronized to the XFEL.

        PreLaserTrig : int
            Add a pre-laser trigger to the experimental ('During') sequence
            that occurs N x 8.4 ms before the laser shot. Used to trigger slow 
            diagnostics, shutters, etc.

        SlowCam : bool
            Add the slow cameras (i.e. PI-MTEs, Pixis) to the sequence.

        SlowCamDelay : int
            The number of beam codes to delay the sequence to allow the slow
            cameras to open their shutters.
        """

        # Requested config 
        self.prelasertrig = int(PreLaserTrig)
        self.slowcam = SlowCam
        self.slowcamdelay = SlowCamDelay
        self.rate = int(Rate)


    def darkSequence(self, nshots, preshot=True):
        """Setup a dark sequence (no XFEL, no optical laser).

        darkSequence(preshot=True)

        Parameters
        ----------
        nshots : int
            The number of events to take during the dark sequence.

        preshot : bool
            Set the mark event code. Uses pre-shot (EC 170) if True, 
            post-shot (EC 171) if false.
        """

        seq = []

        bd = int(120/self.rate) # Beam deltas

        # Decide what marker to use
        if preshot:
            mark = self.EC['prelaser']
        else:
            mark = self.EC['postlaser']

        # Setup first shot
        eventcodes = []
        eventcodes.append([self.EC['daqreadout'], 0])
        eventcodes.append([mark, 0])
        if self.slowcam:
            eventcodes.append([self.EC['slowcam'], self.slowcamdelay])
        if self.prelasertrig > 0:
            eventcodes.append([self.EC['prelasertrig'], self.prelasertrig])

        seq = generateSequence(eventcodes, bd)

        if nshots > 1:
            # Create sequence for all but last shot
            eventcodes = []
            eventcodes.append([self.EC['daqreadout'], 0])
            eventcodes.append([mark, 0])
            if self.prelasertrig > 0:
                eventcodes.append([self.EC['prelasertrig'], self.prelasertrig])

            s = generateSequence(eventcodes, bd)
            s *= nshots-1
            seq += s

            #seq += generateSequence(eventcodes, bd)

        return seq

    def darkXraySequence(self, nshots, preshot=True):
        """Setup a dark X-ray sequence (XFEL only, no optical laser).

        darkXraySequence(nshots, preshot=True)

        Parameters
        ----------
        nshots : int
            The number of events to take during the dark sequence.

        preshot : bool
            Set the mark event code. Uses pre-shot (EC 170) if True, 
            post-shot (EC 171) if false.
        """

        seq = []

        bd = int(120/self.rate) # Beam deltas per xray shot

        # Decide what marker to use
        if preshot:
            mark = self.EC['prelaser'] 
        else:
            mark = self.EC['postlaser']

        # Setup first shot
        eventcodes = []
        eventcodes.append([self.EC['pulsepicker'], 2])
        eventcodes.append([mark, 0])
        eventcodes.append([self.EC['daqreadout'], 0])
        if self.slowcam:
            eventcodes.append([self.EC['slowcam'], self.slowcamdelay])
        if self.prelasertrig > 0:
            eventcodes.append([self.EC['prelasertrig'], self.prelasertrig])

        seq = generateSequence(eventcodes, bd)

        if nshots > 1:
            # Create sequence for all but last shot
            eventcodes = []
            eventcodes.append([self.EC['pulsepicker'], 2])
            eventcodes.append([mark, 0])
            eventcodes.append([self.EC['daqreadout'], 0])
            if self.prelasertrig > 0:
                eventcodes.append([self.EC['prelasertrig'], self.prelasertrig])

            s = generateSequence(eventcodes, bd)
            s *= nshots-2
            seq += s

            # Add in the last shot
            eventcodes = []
            eventcodes.append([self.EC['pulsepicker'], 1])
            eventcodes.append([mark, 0])
            eventcodes.append([self.EC['daqreadout'], 0])
            if self.prelasertrig > 0:
                eventcodes.append([self.EC['prelasertrig'], self.prelasertrig])

            seq += generateSequence(eventcodes, bd)

        return seq

    def opticalSequence(self, nshots, laser, preshot=True):
        """Set up an optical laser sequence (no XFEL, optical laser only).

        opticalSequence(nshots, laser, preshot=True)

        Parameters
        ----------
        nshots : int
            The number of events to take during the optical sequence.

        laser : str
            Select which laser you want to fire. 'longpulse' for NS laser,
            'shortpulse' for FS laser.

        preshot : bool
            Set the mark event code. Uses pre-shot (EC 170) if True, 
            post-shot (EC 171) if false.
        """

        if laser != 'longpulse' and laser != 'shortpulse':
            raise Exception("Unrecognized laser requested: {}".format(laser))

        if laser == 'longpulse' and nshots > 1:
            m = ("Cannot take more than one shot with the long pulse laser! "
                "Please set the number of shots to 1.")
            raise Exception(m)

        lasercode = self.EC[laser]

        seq = []

        bd = int(120/self.rate) # Beam deltas per xray shot

        # Decide what marker to use
        if preshot:
            mark = self.EC['prelaser'] 
        else:
            mark = self.EC['postlaser']
           
        # Setup first shot
        eventcodes = []
        eventcodes.append([self.EC['daqreadout'], 0])
        eventcodes.append([lasercode, 0])
        eventcodes.append([mark, 0])
        if self.slowcam:
            eventcodes.append([self.EC['slowcam'], self.slowcamdelay])
        if self.prelasertrig > 0:
            eventcodes.append([self.EC['prelasertrig'], self.prelasertrig])

        seq = generateSequence(eventcodes, bd)

        if nshots > 1:
            # Create sequence for all but last shot
            eventcodes = []
            eventcodes.append([self.EC['daqreadout'], 0])
            eventcodes.append([lasercode, 0])
            eventcodes.append([mark, 0])
            if self.prelasertrig > 0:
                eventcodes.append([self.EC['prelasertrig'], self.prelasertrig])

            s = generateSequence(eventcodes, bd)
            s *= nshots-1
            seq += s

        return seq

    def duringSequence(self, nshots, laser):
        """Setup a 'during' sequence (optical laser + XFEL).

        """
        bd = int(120/self.rate) # Beam deltas per laser shot

        if laser != 'longpulse' and laser != 'shortpulse':
            raise Exception("Unrecognized laser requested: {}".format(laser))

        if laser == 'longpulse' and nshots > 1:
            m = ("Cannot take more than one shot with the long pulse laser! "
                "Please set the number of shots to 1.")
            raise Exception(m)

        lasercode = self.EC[laser]

        # Setup first shot
        eventcodes = []
        eventcodes.append([self.EC['pulsepicker'], 2])
        eventcodes.append([self.EC['daqreadout'], 0])
        eventcodes.append([lasercode, 0])
        if self.slowcam:
            eventcodes.append([self.EC['slowcam'], self.slowcamdelay])
        if self.prelasertrig > 0:
            eventcodes.append([self.EC['prelasertrig'], self.prelasertrig])

        seq = generateSequence(eventcodes, bd)

        if nshots > 1:
            # Create sequence for all but last shot
            eventcodes = []
            eventcodes.append([self.EC['pulsepicker'], 2])
            eventcodes.append([self.EC['daqreadout'], 0])
            eventcodes.append([lasercode, 0])
            if self.prelasertrig > 0:
                eventcodes.append([self.EC['prelasertrig'], self.prelasertrig])

            s = generateSequence(eventcodes, bd)
            s *= nshots-2
            seq += s

            # Add in the last shot
            eventcodes = []
            eventcodes.append([self.EC['pulsepicker'], 1])
            eventcodes.append([self.EC['daqreadout'], 0])
            eventcodes.append([lasercode, 0])
            if self.prelasertrig > 0:
                eventcodes.append([self.EC['prelasertrig'], self.prelasertrig])

            seq += generateSequence(eventcodes, bd)
            
        return seq

