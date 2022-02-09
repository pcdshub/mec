import time
#from mec.laser import NanoSecondLaser
from mec.db import shutter1, shutter2, shutter3, shutter4, shutter5, shutter6
from mec.db import seq

class User():
    #nsl = NanoSecondLaser()

    #def optical_only(self):
    #    self.nsl.during = 0
    #    self.nsl.preo = 1

    def shutters_close(self):
        shutter1.close()
        shutter2.close()
        shutter3.close()
        shutter4.close()
        shutter5.close()
        shutter6.close()

    def shutters_open(self):
        shutter1.open()
        shutter2.open()
        shutter3.open()
        shutter4.open()
        shutter5.open()
        shutter6.open()

    def shot(self):
        print("Closing the shutters, please wait...")
        self.shutters_close()
        time.sleep(5)
        print("Taking a shot, please wait...")
        seq.play_control.put(1)
        time.sleep(15)
        print("Opening the shutters, please wait...")
        self.shutters_open()

    def save_pin(self):
        target.x.presets.add_here_exp('pin', commment='current x pin position')
        target.y.presets.add_here_exp('pin', commment='current y pin position')
