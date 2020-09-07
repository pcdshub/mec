#!/usr/bin/env python
#
# Module for the MEC laser systems.
#

import logging
import time
import logging
from bluesky.plans import count
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from mec.db import seq, daq
from mec.db import shutter1, shutter2, shutter3, shutter4, shutter5, shutter6
from mec.db import mec_pulsepicker as pp
from .sequence import Sequence

logger = logging.getLogger(__name__)

class Laser():
    """Base class for the MEC laser systems."""
    def __init__(self, Laser, Rate=5, PreDark=0, PreX=0, PreO=0, PostDark=0, PostX=0, 
                 PostO=0, During=1, PreLaserTrig=0, SlowCam=False,
                 SlowCamDelay=5, Shutters=[1,2,3,4,5,6]):

        self._config = {'laser': Laser,
                        'rate': int(Rate),
                        'predark': int(PreDark),
                        'prex': int(PreX),
                        'preo': int(PreO),
                        'postdark': int(PostDark),
                        'postx': int(PostX),
                        'posto': int(PostO),
                        'during': int(During),
                        'prelasertrig': int(PreLaserTrig),
                        'slowcam': SlowCam,
                        'slowcamdelay': int(SlowCamDelay),
                        'shutters': Shutters}
        
        self._seq = Sequence()
        self._shutters = {1: shutter1, 
                          2: shutter2,
                          3: shutter3,
                          4: shutter4,
                          5: shutter5,
                          6: shutter6}

        self._sync_markers = {0.5:0, 1:1, 5:2, 10:3, 30:4, 60:5, 120:6, 360:7}

    @property
    def config(self):
        """Return the current configuration of the laser."""
        conf = self._config.copy()

        return conf

    @property
    def __laser(self):
        """The laser to run (short pulse or long pulse). SHOULD NOT BE 
        CONFIGURED EXCEPT AT INIT. DON'T TOUCH THIS UNLESS YOU KNOW WHAT YOU'RE
        DOING."""
        return self._config['laser']

    @__laser.setter
    def __laser(self, value):
        self._config['laser'] = value

    @property
    def __rate(self):
        """The operation rate of the laser. Used to configure the event 
        sequencer sync marker. SHOULD NOT BE CONFIGURED EXCEPT AT INIT.
        DON'T TOUCH THIS UNLESS YOU KNOW WHAT YOU'RE DOING."""
        return self._config['rate']

    @__rate.setter
    def __rate(self, value):
        self._config['rate'] = value

    @property
    def predark(self):
        """The number of pre-dark shots to take for a given sequence."""
        return int(self._config['predark'])

    @predark.setter
    def predark(self, value):
        self._config['predark'] = int(value)

    @property
    def prex(self):
        """The number of pre-xray shots to take for a given sequence."""
        return int(self._config['prex'])

    @prex.setter
    def prex(self, value):
        self._config['prex'] = int(value)

    @property
    def preo(self):
        """The number of pre-optical shots to take for a given sequence."""
        return int(self._config['preo'])

    @preo.setter
    def preo(self, value):
        self._config['preo'] = int(value)

    @property
    def postdark(self):
        """The number of post-dark shots to take for a given sequence."""
        return int(self._config['postdark'])

    @postdark.setter
    def postdark(self, value):
        self._config['postdark'] = int(value)

    @property
    def postx(self):
        """The number of post-xray shots to take for a given sequence."""
        return int(self._config['postx'])

    @postx.setter
    def postx(self, value):
        self._config['postx'] = int(value)

    @property
    def posto(self):
        """The number of post-optical shots to take for a given sequence."""
        return int(self._config['posto'])

    @posto.setter
    def posto(self, value):
        self._config['posto'] = int(value)

    @property
    def during(self):
        """The number of 'during' (optical + x-ray)  shots to take for a given 
        sequence."""
        return int(self._config['during'])

    @during.setter
    def during(self, value):
        self._config['during'] = int(value)

    @property
    def prelasertrig(self):
        """The number (N) of N x 8.4 ms multiples to wait before the optical
        laser shot. Used to trigger slow diagnostics, shutters, etc. Default
        is 0."""
        return int(self._config['prelasertrig'])

    @prelasertrig.setter
    def prelasertrig(self, value):
        self._config['prelasertrig'] = int(value)

    @property
    def slowcam(self):
        """Option to add in the PI-MTE, Pixis 'slow' cameras devices to the
        optical sequence. Default is False."""
        return self._config['slowcam']

    @slowcam.setter
    def slowcam(self, value):
        self._config['slowcam'] = bool(value)

    @property
    def slowcamdelay(self):
        """The integer number of beam codes to delay the sequence to allow the
        slow cameras to open their shutters. Default is 5; this should not
        usually be changed."""
        return self._config['slowcamdelay']

    @slowcamdelay.setter
    def slowcamdelay(self, value):
        self._config['slowcamdelay'] = int(value)

    @property
    def shutters(self):
        """The MEC target chamber shutters to close on shot. Default is all of
        them (1 through 6). Configure this setting by providing a list of
        shutters to close prior to the shot, e.g. laser.shutters = [1,2,4,6]"""
        return self._config['shutters']

    @shutters.setter
    def shutters(self, value):
        allowed = [1,2,3,4,5,6]
        new_shutters = []
        for v in value:
            if v in allowed:
                new_shutters.append(int(v))
            else:
                print("Unrecognized shutter {}. Skipping...".format(v))
        self._config['shutters'] = new_shutters

    def configure(self, conf):
        """Configure the laser for the given parameters.

        Laser(conf)

        Parameters
        ----------
        conf : dict
            A dictionary containing the configuration of the laser. This
            dictionary takes the following form:
                conf = {'laser': <laser>,
                        'rate': <rate>,
                        'predark': <predark>,
                        'prex': <prex>,
                        'preo': <preo>,
                        'postdark': <postdark>,
                        'postx': <postx>,
                        'posto': <posto>,
                        'during': <during>,
                        'prelasertrig': <prelasertrig>,
                        'slowcam': <slowcam>,
                        'slowcamdelay': <slowcamdelay>,
                        'shutters'= <shutters>}

                Default configuration:
                    Rate=5,
                    PreDark=0,
                    PreX=0,
                    PreO=0,
                    PostDark=0,
                    PostX=0, 
                    PostO=0,
                    During=1,
                    PreLaserTrig=0,
                    SlowCam=False,
                    SlowCamDelay=5,
                    Shutters=[1,2,3,4,5,6]

            This method can be given a subset of these parameters. The method
            will only apply recognized parameters that are supplied, and will
            use the current values for parameters that are not supplied.
 
            Configuration Definitions
            ------------------------- 
            Laser : string
                The laser that you want to shoot. There are two options:
                'shortpulse', and 'longpulse'. THIS SHOULD NOT BE CONFIGURED
                EXCEPT AT INIT.

            Rate : int
                Integer rate at which you want to take laser shots, with or
                without x-rays, synchronized to the XFEL. THIS SHOULD NOT BE 
                CONFIGURED EXCEPT AT INIT.

            PreDark : int
                Record dark shots (no XFEL, no optical laser) prior to the
                X-ray + optical laser shot.

            PreX : int
                Record dark X-ray only shots (no optical laser) prior to the
                X-ray + optical laser shot.

            PreO : int
                Record optical only laser shots (no XFEL) prior to the X-ray +
                optical laser shot.

            PostDark : int
                Record dark shots (no XFEL, no optical laser) after the X-ray +
                optical laser shot.

            PostX : int
                Record dark X-ray only shots (no optical laser) after the X-ray 
                + optical laser shot.

            PostO : int
                Record optical only laser shots (no XFEL) after the X-ray +
                optical laser shot.

            During : int
                Record optical laser + X-ray laser shots. 

            PreLaserTrig : int
                Add a pre-laser trigger to the  sequence that occurs
                approximately N x 8.4 ms before the laser shot. Used to trigger
                slow diagnostics, shutters, etc.

            SlowCam : bool
                Add the slow cameras (i.e. PI-MTEs, Pixis) to the sequence.

            SlowCamDelay : int
                The number of beam codes to delay the sequence to allow the slow
                cameras to open their shutters.
    
            Shutters : list
                The shutters that must be closed prior to taking the laser shot.
                This is used to protect cameras and other diagnostics from the
                shot. Defaults to all shutters ([1,2,3,4,5,6]).        
        """

        for key in conf.keys():
            if key in self._config.keys():
                if key in ['laser', 'rate']:
                    # Not allowed to configure these except at init. Skip.
                    pass
                else:
                    self._config[key] = conf[key]
            else:
                print("Unrecognized key: {}. Skipping ... ".format(key))

        seq_conf = {'rate': self._config['rate'],
                    'prelasertrig': self._config['prelasertrig'],
                    'slowcam': self._config['slowcam'],
                    'slowcamdelay': self._config['slowcamdelay']}

        self._seq.configure(Rate=seq_conf['rate'], 
                            PreLaserTrig=seq_conf['prelasertrig'],
                            SlowCam=seq_conf['slowcam'],
                            SlowCamDelay=seq_conf['slowcamdelay'])

    def _single_shot_plan(self, record=True, use_l3t=False, controls=[],
                           end_run=True):
        """Definition of plan for taking laser shots with the MEC laser."""
        # TODO: Add attenuator control

        logging.debug("Generating shot plan using _shot_plan.")
        logging.debug("_shot_plan config:")
        logging.debug("{}".format(self._config))
        logging.debug("Record: {}".format(record))
        logging.debug("use_l3t: {}".format(use_l3t))
        logging.debug("controls: {}".format(controls))

        # Make sure that any updates to configuration are applied
        self.configure(self._config)

        # Check number of shots for long pulse laser
        if self._config['laser'] == 'longpulse':
            lpl_shots = self._config['preo'] + self._config['during'] + \
                        self._config['posto']

            if lpl_shots > 1:
                m = ("Cannot shoot the long pulse laser more than once in a "
                     "sequence! Please reduce the number of optical shots "
                     "requested to 1!")
                raise Exception(m)

        # Setup the daq based on config
        total_shots = self._config['predark'] + self._config['prex'] + \
                      self._config['preo'] + self._config['postdark'] + \
                      self._config['postx'] + self._config['posto'] + \
                      self._config['during']

        print("Configured for {} total shots.".format(total_shots))
        logging.debug("Total shots: {}".format(total_shots))
    
        yield from bps.configure(daq, begin_sleep=2, record=record, use_l3t=use_l3t, controls=controls)

        # Add sequencer, DAQ to detectors for shots
        dets = [daq, seq]

        for det in dets:
            yield from bps.stage(det)

        # Check for slow cameras, stage if requested
        if self._config['slowcam']:
            from .slowcams import SlowCameras
            self._slowcams = SlowCameras()
            dets.append(self._slowcams) # Add this in to auto-unstage later
            yield from bps.stage(self._slowcams)

        # Setup the pulse picker for single shots in flip flop mode
        pp.flipflop(wait=True)

        # Setup sequencer for requested rate
        sync_mark = int(self._sync_markers[self._config['rate']])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(0) # Run sequence once

        # Dark (no optical laser, no XFEL) shots
        if self._config['predark'] > 0:
            # Get number of predark shots
            shots = self._config['predark']
            logging.debug("Configuring for {} predark shots".format(shots))
            yield from bps.configure(daq, events=shots)

            # Preshot dark, so use preshot laser marker
            pre_dark_seq = self._seq.darkSequence(shots, preshot=True)
            seq.sequence.put_seq(pre_dark_seq)

            # Number of shots is determined by sequencer, so just trigger/read
            print("Taking {} predark shots ... ".format(self._config['predark']))
            yield from bps.trigger_and_read(dets)

        # Pre-xray (no optical laser, XFEL only) shots
        if self._config['prex'] > 0:
            # Get number of prex shots
            shots = self._config['prex']
            logging.debug("Configuring for {} prex shots".format(shots))
            yield from bps.configure(daq, events=shots)

            # Preshot x-ray only shots, so use preshot laser marker
            prex_seq = self._seq.darkXraySequence(shots, preshot=True)
            seq.sequence.put_seq(prex_seq)

            # Number of shots is determined by sequencer, so just trigger/read
            print("Taking {} prex shots ... ".format(shots))
            yield from bps.trigger_and_read(dets)
            
        # Pre-optical (optical laser only, no XFEL) shots
        if self._config['preo'] > 0:
            # Get number of preo shots
            shots = self._config['preo']
            logging.debug("Configuring for {} preo shots".format(shots))
            yield from bps.configure(daq, events=shots)

            # Optical only shot, with defined laser
            preo_seq = self._seq.opticalSequence(shots, self._config['laser'],\
                                                 preshot=True)
            seq.sequence.put_seq(preo_seq)

            # Number of shots is determined by sequencer, so just take 1 count
            print("Taking {} preo shots ... ".format(shots))
            yield from bps.trigger_and_read(dets)

        # 'During' (optical laser + XFEL) shots
        if self._config['during'] > 0:
            # Get number of during shots
            shots = self._config['during']
            logging.debug("Configuring for {} during shots".format(shots))
            yield from bps.configure(daq, events=shots)

            # During shot, with defined laser
            during_seq = self._seq.duringSequence(shots, self._config['laser'])
            seq.sequence.put_seq(during_seq)

            # Number of shots is determined by sequencer, so just take 1 count
            print("Taking {} during shots ... ".format(shots))
            yield from bps.trigger_and_read(dets)

        # Post-optical (optical laser only, no XFEL) shots
        if self._config['posto'] > 0:
            # Get number of post optical shots
            shots = self._config['posto']
            logging.debug("Configuring for {} posto shots".format(shots))
            yield from bps.configure(daq, events=shots)

            # Optical only shot, with defined laser
            posto_seq = self._seq.opticalSequence(shots, self._config['laser'],\
                                                  preshot=False)
            seq.sequence.put_seq(posto_seq)

            # Number of shots is determined by sequencer, so just take 1 count
            print("Taking {} posto shots ... ".format(shots))
            yield from bps.trigger_and_read(dets)

        # Post-xray (no optical laser, XFEL only) shots
        if self._config['postx'] > 0:
            # Get number of postx shots
            shots = self._config['postx']
            logging.debug("Configuring for {} postx shots".format(shots))
            yield from bps.configure(daq, events=shots)

            # Postshot x-ray only shots, so use postshot laser marker
            postx_seq = self._seq.darkXraySequence(shots, preshot=False)
            seq.sequence.put_seq(postx_seq)

            # Number of shots is determined by sequencer, so just take 1 count
            print("Taking {} postx shots ... ".format(shots))
            yield from bps.trigger_and_read(dets)
            
        # Dark (no optical laser, no XFEL) shots
        if self._config['postdark'] > 0:
            # Get number of postdark shots
            shots = self._config['postdark']
            logging.debug("Configuring for {} postdark shots".format(shots))
            yield from bps.configure(daq, events=shots)

            # Postshot dark, so use postshot laser marker
            post_dark_seq = self._seq.darkSequence(shots, preshot=False)
            seq.sequence.put_seq(post_dark_seq)

            # Number of shots is determined by sequencer, so just take 1 count
            print("Taking {} postdark shots ... ".format(shots))
            yield from bps.trigger_and_read(dets)

        
        for det in dets:
            yield from bps.unstage(det)

        if end_run:
            daq.end_run()

    def shot(self, record=True, use_l3t=False, controls=[], end_run=True):
        """Return a plan for executing a laser shot (or shots), based on the 
        current configuration of the laser. To modify the shot, update the
        laser configuration, then call this method. This method uses the pulse
        picker and sequencer to take XFEL + Optical laser shots. Multiple XFEL
        and/or laser shots will be performed by setting up the sequencer for
        a multiple shots, and running the sequence once.

        laser.shot(record=True)

        Parameters
        ----------
        record : bool
            Select whether the run will be recorded or not. Defaults to True.

        use_l3t : bool
            Select whether the run will use a level 3 trigger or not. Defaults
            to False.

        controls : list
            List of controls devices to include values into the DAQ data stream
            as variables. All devices must have a name attribute. Defaults to
            empty list.

        end_run : bool
            Select whether or not to end the run after the shot. Defaults to
            True.

        Examples
        --------
        # Take a shot immediately, don't record

        RE(laser.shot(record=False))

        # Take a shot immediately, record

        RE(laser.shot(record=True))

        # Initialize the shot, record a shot at some later time when RE(p) is
        # called. 

        p = laser.shot(record=True)
        ...
        RE(p)
        """

        dev = []
        for shutter in self._config['shutters']:
            dev.append(self._shutters[shutter])

        @bpp.stage_decorator(dev)
        @bpp.run_decorator()
        def inner(record, use_l3t, controls, end_run):
            plan = self._single_shot_plan(record, use_l3t, controls, end_run)

            return plan

        return inner(record, use_l3t, controls, end_run)

class NanoSecondLaser(Laser):
    """Class for the MEC nanosecond laser."""
    def __init__(self):
        laser = 'longpulse'
        super().__init__(laser, Rate=10)

    def __charge(self):
        """Charge the PFN racks for longpulse laser."""
        #TODO
        raise NotImplementedError("This method is not implemented yet!")

class FemtoSecondLaser(Laser):
    """Class for the MEC femtosecond laser."""
    def __init__(self, *args, **kwargs):
        laser = 'shortpulse'
        super().__init__(laser, *args, Rate=5, **kwargs)

    def _grid_scan_plan(self, motor1, m1_start, m1_end, m1_steps,
                               motor2, m2_start, m2_end, m2_steps,
                               record=True, use_l3t=False, controls=[],
                               end_run=True, carriage_return=True):
        # Log stuff
        logging.debug("Returning _grid_scan with the following parameters:")
        logging.debug("m1_start: {}".format(m1_start))
        logging.debug("m1_end: {}".format(m1_end))
        logging.debug("m2_steps: {}".format(m1_steps))
        logging.debug("m2_start: {}".format(m2_start))
        logging.debug("m2_end: {}".format(m2_end))
        logging.debug("m2_steps: {}".format(m2_steps))
        logging.debug("end_run: {}".format(end_run))
        logging.debug("carriage_return: {}".format(carriage_return))

        m1_step_size = (m1_end-m1_start)/(m1_steps-1)
        logging.debug("m1 step size: {}".format(m1_step_size))
        m2_step_size = (m2_end-m2_start)/(m2_steps-1)
        logging.debug("m2 step size: {}".format(m2_step_size))
        for i in range(m2_steps):
            new_m2 = m2_start+m2_step_size*i
            logging.debug("Moving motor2 to {}".format(new_m2))
            yield from bps.mv(motor2, new_m2)
            for j in range(m1_steps):
                new_m1 = m1_start+m1_step_size*j
                logging.debug("Moving motor1 to {}".format(new_m1))
                yield from bps.mv(motor1, new_m1)
                logging.debug("Calling self._single_shot_plan...")
                yield from self._single_shot_plan(record, use_l3t, controls,
                                                   False)
                # If this is the last move in the scan, check cleanup settings
                if (i == (m1_steps-1)) and (j == (m2_steps -1)):
                    if carriage_return: # Then go back to start
                        yield from bps.mv(motor1, m1_start)
                        yield from bps.mv(motor2, m2_start)
                    if end_run:
                        daq.end_run()

    def grid_scan_shot(self, motor1, m1_start, m1_end, m1_steps,
                       motor2, m2_start, m2_end, m2_steps,
                       record=True, use_l3t=False, controls=[], end_run=True,
                       carriage_return=True):
        """Return a plan for scanning a motor, taking a shot at each point."""

        dev = []
        for shutter in self._config['shutters']:
            dev.append(self._shutters[shutter])

        @bpp.stage_decorator(dev)
        @bpp.run_decorator()
        def inner(motor1, m1_start, m1_end, m1_steps,
                  motor2, m2_start, m2_end, m2_steps,
                  record, use_l3t, controls, end_run, carriage_return):
            plan = self._grid_scan_plan(motor1, m1_start, m1_end, m1_steps,
                                         motor2, m2_start, m2_end, m2_steps,
                                         record, use_l3t, controls, end_run,
                                         carriage_return)

            return plan

        return inner(motor1, m1_start, m1_end, m1_steps,
                     motor2, m2_start, m2_end, m2_steps,
                     record, use_l3t, controls, end_run, carriage_return)

    def _1D_fly_scan(self, motor, start, end, record, use_l3t, controls,
                     end_run, carriage_return, predelay, postdelay):
                      
        """Plan for setting up a one-dimensional fly scan."""

        logging.debug("Generating 1D fly scan shot plan using _1D_fly_scan.")
        logging.debug("_shot_plan config:")
        logging.debug("{}".format(self._config))
        logging.debug("motor: {}".format(motor))
        logging.debug("start: {}".format(start))
        logging.debug("end: {}".format(end))
        logging.debug("predelay: {}".format(predelay))
        logging.debug("postdelay: {}".format(postdelay))
        logging.debug("Record: {}".format(record))
        logging.debug("use_l3t: {}".format(use_l3t))
        logging.debug("controls: {}".format(controls))
        logging.debug("carriage_return: {}".format(carriage_return))
        logging.debug("end_run: {}".format(end_run))

        # Adjust start/end for any pre/post-delays
        if bool(predelay):
            if (end-start) >= 0:
                start -= predelay
            else:
                start += predelay

        if bool(postdelay):
            if (end-start) >= 0:
                end += postdelay
            else:
                end -= postdelay

        m_velo = motor.velocity.get()
        # Total number of events: (mm/(mm/s))*(events/s) = events
        nevents = int((abs(end-start)/m_velo)*self.config['rate'])

        shot_type_count = 0
        shot_types = ['predark', 'prex', 'preo', 'postdark', 'postx', 'posto',
                      'during']

        # Look for more than one shot type (should only set up sequencer for
        # one shot type at a time in this operation mode).
        old_config = self.config
        new_config = self.config
        for shot_type in shot_types:
            if bool(self.config[shot_type]):
                shot_type_count += 1
                if shot_type_count >= 2:
                    self.configure(old_config)
                    raise ValueError("Cannot have more than one type of shot "
                                     "for a given 1D scan! Please change the "
                                     "laser configuration to have only one "
                                     "shot type!")
                new_config[shot_type] = nevents

        if shot_type_count == 1:
            # Found only one shot type; valid shot
            self.configure(new_config)
        else:
            # Something is weird
            raise Exception("Please configure the laser for one shot type! "
                            "The configuration is invalid!")
        
        # Get into initial position
        yield from bps.mv(motor, start)

        #yield from bps.mv(motor, end) # Can't do this since bps.mv waits
                                       # for completion. :(
                                       # Make update to bps.mv?
        motor.mv(end)
        # Shoot stuff
        yield from self._single_shot_plan(record=record, use_l3t=use_l3t,
                                          controls=controls, end_run=end_run)

        if carriage_return:
            yield from bps.mv(motor, start)
        if end_run:
            daq.end_run()

    def fly_scan_1D_shot(self, motor, start, end, record=True, use_l3t=False,
                         controls=[], end_run=True, carriage_return=True,
                         predelay=None, postdelay=None):
        """Return a plan for doing a 1D fly scan with the laser, continuously
        taking shots along the way."""
        dev = []
        for shutter in self._config['shutters']:
            dev.append(self._shutters[shutter])

        @bpp.stage_decorator(dev)
        @bpp.run_decorator()
        def inner(motor, start, end, record, use_l3t, controls, end_run,
                  carriage_return, predelay, postdelay):

            plan = self._1D_fly_scan(motor, start, end, record,
                                     use_l3t, controls, end_run,
                                     carriage_return, predelay, postdelay)

            return plan

        return inner(motor, start, end, record, use_l3t, controls, end_run,
                     carriage_return, predelay, postdelay)

    def _2D_fly_scan_plan(self, motor1, m1_start, m1_end, motor2, m2_start,
                          m2_end, m2_steps, predelay, postdelay, record, 
                          use_l3t, controls, end_run, carriage_return):
        # Log stuff
        logging.debug("Returning _2D_fly_scan with the following parameters:")
        logging.debug("m1_start: {}".format(m1_start))
        logging.debug("m1_end: {}".format(m1_end))
        logging.debug("m2_start: {}".format(m2_start))
        logging.debug("m2_end: {}".format(m2_end))
        logging.debug("m2_steps: {}".format(m2_steps))
        logging.debug("end_run: {}".format(end_run))
        logging.debug("carriage_return: {}".format(carriage_return))

        m2_step_size = (m2_end-m2_start)/(m2_steps-1)
        logging.debug("m2 step size: {}".format(m2_step_size))
        for i in range(m2_steps):
            new_m2 = m2_start+m2_step_size*i
            logging.debug("Moving motor2 to {}".format(new_m2))
            yield from bps.mv(motor2, new_m2)
            logging.debug("Calling self._1D_fly_scan...")
            yield from self._1D_fly_scan(motor1, m1_start, m1_end, record, 
                                         use_l3t, controls, False, 
                                         carriage_return, predelay, postdelay)
            #yield from self._single_shot_plan(record, use_l3t, controls,
            #                                   False)
            # Last move in the scan, so check cleanup settings
            #if j == (m2_steps-1):
        if carriage_return:
            yield from bps.mv(motor1, m1_start)
            yield from bps.mv(motor2, m2_start)
        if end_run:
            daq.end_run()

    def fly_scan_2D_shot(self, motor1, m1_start, m1_end, motor2, m2_start,
                         m2_end, m2_steps, predelay=None, postdelay=None,
                         record=True, use_l3t=False, controls=[], end_run=True,
                         carriage_return=True):
        """Return a plan for doing a 2D fly scan with the laser, continuously
        taking shots along the way."""
        
        dev = []
        for shutter in self._config['shutters']:
            dev.append(self._shutters[shutter])

        @bpp.stage_decorator(dev)
        @bpp.run_decorator()
        def inner(motor1, m1_start, m1_end, motor2, m2_start, m2_end, m2_steps,
                  predelay, postdelay, record, use_l3t, controls, end_run,
                  carriage_return):

            plan = self._2D_fly_scan_plan(motor1, m1_start, m1_end, motor2, 
                                          m2_start, m2_end, m2_steps, predelay,
                                          postdelay, record, use_l3t, controls,
                                          end_run, carriage_return)

            return plan

        return inner(motor1, m1_start, m1_end, motor2, m2_start, m2_end, 
                     m2_steps, predelay, postdelay, record, use_l3t, controls,
                     end_run, carriage_return)

class DualLaser(Laser):
    """
    Class for firing both the shortpulse and longpulse lasers at the same
    time.
    """
    def __init__(self):
        laser = 'dual'
        super().__init__(laser, Rate=10, PreDark=0, PreX=0, PreO=0, PostDark=0,
                         PostX=0, PostO=0, During=0, PreLaserTrig=0, 
                         SlowCam=False, SlowCamDelay=5, Shutters=[1,2,3,4,5,6])

    def _single_shot_plan(self, record=True, use_l3t=False, controls=[],
                           end_run=True):
        """Definition of plan for taking laser shots with the MEC laser."""
        # TODO: Add attenuator control

        logging.debug("Generating shot plan using _shot_plan.")
        logging.debug("_shot_plan config:")
        logging.debug("{}".format(self._config))
        logging.debug("Record: {}".format(record))
        logging.debug("use_l3t: {}".format(use_l3t))
        logging.debug("controls: {}".format(controls))

        # Make sure that any updates to configuration are applied
        self.configure(self._config)

        # Setup the daq based on config
        total_shots = 1

        print("Configured for {} total shots.".format(total_shots))
        logging.debug("Total shots: {}".format(total_shots))
    
        yield from bps.configure(daq, begin_sleep=2, record=record, use_l3t=use_l3t, controls=controls)

        # Add sequencer, DAQ to detectors for shots
        dets = [daq, seq]

        for det in dets:
            yield from bps.stage(det)

        # Check for slow cameras, stage if requested
        if self._config['slowcam']:
            from .slowcams import SlowCameras
            self._slowcams = SlowCameras()
            dets.append(self._slowcams) # Add this in to auto-unstage later
            yield from bps.stage(self._slowcams)

        # Setup the pulse picker for single shots in flip flop mode
        pp.flipflop(wait=True)

        # Setup sequencer for requested rate
        sync_mark = int(self._sync_markers[self._config['rate']])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(0) # Run sequence once

        # Dual (FSL + NSL + XFEL) shots
        shots = total_shots
        logging.debug("Configuring for {} dual shots".format(shots))
        yield from bps.configure(daq, events=shots)

        # Preshot dark, so use preshot laser marker
        dual_seq = self._seq.dualDuringSequence()
        seq.sequence.put_seq(dual_seq)

        # Number of shots is determined by sequencer, so just trigger/read
        print("Taking {} predark shots ... ".format(shots)
        yield from bps.trigger_and_read(dets)

        for det in dets:
            yield from bps.unstage(det)

        if end_run:
            daq.end_run()

    def shot(self, record=True, use_l3t=False, controls=[], end_run=True):
        """
        Return a plan for executing a dual laser shot.

        Parameters
        ----------
        record : bool
            Select whether the run will be recorded or not. Defaults to True.

        use_l3t : bool
            Select whether the run will use a level 3 trigger or not. Defaults
            to False.

        controls : list
            List of controls devices to include values into the DAQ data stream
            as variables. All devices must have a name attribute. Defaults to
            empty list.

        end_run : bool
            Select whether or not to end the run after the shot. Defaults to
            True.

        Examples
        --------
        # Take a shot immediately, don't record

        RE(laser.shot(record=False))

        # Take a shot immediately, record

        RE(laser.shot(record=True))

        # Initialize the shot, record a shot at some later time when RE(p) is
        # called. 

        p = laser.shot(record=True)
        ...
        RE(p)
        """

        dev = []
        for shutter in self._config['shutters']:
            dev.append(self._shutters[shutter])

        @bpp.stage_decorator(dev)
        @bpp.run_decorator()
        def inner(record, use_l3t, controls, end_run):
            plan = self._single_shot_plan(record, use_l3t, controls, end_run)

            return plan

        return inner(record, use_l3t, controls, end_run)
