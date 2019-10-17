#!/usr/bin/env python
#
# Module for experiment lu6017. 

import logging
from hutch_python.utils import safe_load
from mec.db import daq, seq
from mec.db import shutter1, shutter2, shutter3, shutter4, shutter5, shutter6
from mec.slowcams import SlowCameras
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp

logger = logging.getLogger(__name__)

class User():
    def __init__(self):
        with safe_load('Short Pulse Laser'):
            from mec.laser import FemtoSecondLaser
            fsl = FemtoSecondLaser()
            fsl.during = 0
            fsl.predark = 1

        self.shutters = [1,2,3,4,5,6]

        self._sync_markers = {0.5:0, 1:1, 5:2, 10:3, 30:4, 60:5, 120:6, 360:7}
        self._rate = 5
        
        self._shutters = {1: shutter1,
                          2: shutter2,
                          3: shutter3,
                          4: shutter4,
                          5: shutter5,
                          6: shutter6}

    def __single_shot(self, gasdelay=0.05, shotdelay=10.0, record=True,
                      use_l3t=False, controls=[], end_run=True):
        logging.debug("Calling __single_shot with the folling parameters:")
        logging.debug("gasdelay: {}".format(gasdelay))
        logging.debug("shotdelay: {}".format(shotdelay))
        logging.debug("record: {}".format(record))
        logging.debug("use_l3t: {}".format(use_l3t))
        logging.debug("controls: {}".format(controls))
        logging.debug("end_run: {}".format(end_run))

        nshots = 1

        yield from bps.configure(daq, begin_sleep=2, record=record, use_l3t=use_l3t, controls=controls)
        yield from bps.configure(daq, events=nshots)

        # Add sequencer, DAQ to detectors for shots
        dets = [daq, seq]

        for det in dets:
            yield from bps.stage(det)

        # Setup sequencer for requested rate
        sync_mark = int(self._sync_markers[self._rate])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(0) # Run sequence once
    
        # Determine the different sequences needed
        gdelay = int(gasdelay*120)  # 120 beam delays/second    
        sdelay = int(shotdelay*120) # 120 beam delays/second
        slow_cam_seq = [[167, 0, 0, 0]]
        gas_jet_seq = [[177, 0, 0, 0],
                       [176, gdelay, 0, 0],
                       [169, 0, 0, 0],
                       [0, sdelay, 0, 0]]

        s = slow_cam_seq + gas_jet_seq

        logging.debug("Sequence: {}".format(s))
                  
        # Get exposure time in beam deltas from number of shots
        exposure = nshots * (int(shotdelay/120.0) + int(gasdelay/120.0))
        logging.debug("Exposure time: {}".format(exposure*120.0))
        
        # Stage and add in slow cameras *after* daq is staged and configured
        slowcams = SlowCameras()
        # The camera delay and number of 'during' shots are the same in this case (I think)
        config = {'slowcamdelay': exposure, 'during': exposure} 
        dets.append(slowcams) # Add this in to auto-unstage later
        slowcams.stage(config)

        seq.sequence.put_seq(s) 

        yield from bps.trigger_and_read(dets)                

        # If this is the last move in the scan, check cleanup settings
        if end_run:
            daq.end_run() 
       
    def shot(self, gasdelay=0.05, shotdelay=10.0, record=True,
             use_l3t=False, controls=[], end_run=True):
        """
        Single shot script for the LU60 gas jet experiment. 

        Parameters:
        -----------
        gasdelay : float (default: 0.05)
            The number of seconds to wait for the gas jet to be ready after the
            trigger.

        shotdelay : float (default: 10.0)
            The number of seconds to wait between shots. This is empirically
            derived, and is used to allow the chamber pressure to equillibrate
            following a gas jet puff.  

        record : bool (default: True)
            Option to record the scan in the DAQ (or not).

        use_l3t : bool (default: False)
            Option to use a level 3 trigger (or not) in the scan.

        controls : list (default: [])
            Optional list of devices to add to the DAQ data stream. Devices 
            added in this way will have their device.position or device.value
            quantities added to the scan.

        end_run : bool (default: True)
            Option to end the run after the scan. This will cause a new run to
            be initiated during the next scan.

        Examples
        --------
        # Take a shot immediately, don't record

        RE(x.shot(record=False))

        # Take a shot immediately, record

        RE(x.shot(record=True))

        # Initialize the shot, record a shot at some later time when RE(p) is
        # called. 

        p = x.shot(record=True)
        ...
        RE(p)

        """
        dev = []
        for shutter in self.shutters:
            dev.append(self._shutters[shutter])

        @bpp.stage_decorator(dev)
        @bpp.run_decorator()
        def inner(record, use_l3t, controls, end_run):
            plan = self.__single_shot(gasdelay, shotdelay, record, use_l3t,
                                      controls, end_run)

            return plan

        return inner(record, use_l3t, controls, end_run)

    def __jet_scan(self, motor1, m1start, m1end, m1step, motor2, m2start,
                   m2end, m2step, gasdelay=0.05, shotdelay=10.0,
                   record=True, use_l3t=False, controls=[], end_run=True,
                   carriage_return=True):
        """
        Scan for the LU60 gas jet experiment. 

        Parameters:
        -----------
        motor1 : motor
            The first motor on which to run the scan.

        m1start : float
            The position to start the scan for motor1. The motor will travel to
            this position prior to beginning the scan.

        m1end : float
            The position to end the scan on for motor1.

        m1steps : float
            The number of steps for motor 1

        motor2 : motor
            The second motor on which to run the scan.

        m2start : float
            The position to start the scan for motor2. The motor will travel to
            this position prior to beginning the scan.

        m2end : float
            The position to end the scan on for motor 2.

        m2steps : float
            The number of steps for motor 2.

        gasdelay : float (default: 0.05)
            The number of seconds to wait for the gas jet to be ready after the
            trigger.

        shotdelay : float (default: 10.0)
            The number of seconds to wait between shots. This is empirically
            derived, and is used to allow the chamber pressure to equillibrate
            following a gas jet puff.  

        record : bool (default: True)
            Option to record the scan in the DAQ (or not).

        use_l3t : bool (default: False)
            Option to use a level 3 trigger (or not) in the scan.

        controls : list (default: [])
            Optional list of devices to add to the DAQ data stream. Devices 
            added in this way will have their device.position or device.value
            quantities added to the scan.

        end_run : bool (default: True)
            Option to end the run after the scan. This will cause a new run to
            be initiated during the next scan.
        """

        logging.debug("Calling __jet_scan with the folling parameters:")
        logging.debug("motor1: {}".format(motor1))
        logging.debug("m1start: {}".format(m1start))
        logging.debug("m1end: {}".format(m1end))
        logging.debug("m1step: {}".format(m1step))
        logging.debug("motor2: {}".format(motor2))
        logging.debug("m2start: {}".format(m2start))
        logging.debug("m2end: {}".format(m2end))
        logging.debug("m2step: {}".format(m2step))
        logging.debug("gasdelay: {}".format(gasdelay))
        logging.debug("shotdelay: {}".format(shotdelay))
        logging.debug("record: {}".format(record))
        logging.debug("use_l3t: {}".format(use_l3t))
        logging.debug("controls: {}".format(controls))
        logging.debug("end_run: {}".format(end_run))

        nshots = m1steps * m2steps
        logging.debug("nsteps: {}".format(nsteps))
        print("Configured scan for {} steps...".format(nsteps))
        if ((nsteps * 4) + 1) > 2048:
            raise ValueError("The number of steps cannot be greater than 2048!")

        yield from bps.configure(daq, begin_sleep=2, record=record, use_l3t=use_l3t, controls=controls)

        # Add sequencer, DAQ to detectors for shots
        dets = [daq, seq]

        for det in dets:
            yield from bps.stage(det)

        # Setup sequencer for requested rate
        sync_mark = int(self._sync_markers[self._config['rate']])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(0) # Run sequence once
    
        # TODO: determine the different sequences needed.
        gdelay = int(gasdelay*120)  # 120 beam delays/second    
        sdelay = int(shotdelay*120) # 120 beam delays/second
        slow_cam_seq = [[167, 0, 0, 0]]
        gas_jet_seq = [[177, 0, 0, 0],
                       [176, gdelay, 0, 0],
                       [169, 0, 0, 0],
                       [0, sdelay, 0, 0]]
        
        # TODO: Configure the slow cameras
        # Get exposure time in beam deltas from number of shots
        exposure = nshots * (int(shotdelay/120.0) + int(gasdelay/120.0))
        logging.debug("Exposure time: {}".format(exposure))
        
        # Stage and add in slow cameras *after* daq is staged and configured
        slowcams = SlowCameras()
        # The camera delay and number of 'during' shots are the same in this case
        config = {'slowcamdelay': exposure, 'during': exposure} 
        dets.append(slowcams) # Add this in to auto-unstage later
        slowcams.stage(config)

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

                # If this is the first shot, use slow cam in sequence
                if (i == 0) and (j == 0):
                    s = slow_cam_seq + gas_jet_seq
                else:
                    s = gas_jet_seq
                  
                # TODO: set this up to run only if the sequence is different?
                # Do many puts to the test EVG program cause problems? 
                seq.sequence.put_seq(s) 

                
                # If this is the last move in the scan, check cleanup settings
                if (i == (m1_steps-1)) and (j == (m2_steps -1)):
                    if carriage_return: # Then go back to start
                        yield from bps.mv(motor1, m1_start)
                        yield from bps.mv(motor2, m2_start)
                    if end_run:
                        daq.end_run() 
