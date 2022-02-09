#import pypsepics
#import utilities
#from utilitiesMotors import tweak
import time
from numpy import *
from time import time, sleep
class PV2Motor(object):
  def __init__(self,pvmove,pvread,name,sioc_pv=None):
#    Motor.__init__(self,None,name,readbackpv=None,has_dial=False)
    self.name   = name
    self.pvmv = pvmove
    self.pvrd = pvread
    self._sioc_pv=sioc_pv  #pv name of the software ioc. used to reset ioc after reconnect.

  def __call__(self,value=None):
    if value==None: return self.wm()
    else: self.move(value)

  def __repr__(self):
    return self.status()

  def status(self):
    s  = "Pv motor %s\n" % self.name
    s += "  current position %.4g\n" % self.wm()
    return s

  def reset(self):
    if self._sioc_pv==None: print "no SIOC pvname defined. Cannot reset."
    else: pypsepics.put(self._sioc_pv+":SYSRESET",1)
    

  def move_relative(self,howmuch):
    p = self.wm()
    return self.move(p+howmuch)

  def move_silent(self,value): return self.move(value)

  def mvr(self,howmuch): return self.move_relative(howmuch)

  def  move(self,value): return  pypsepics.put(self.pvmv,value)

  def  mv(self,value): return self.move(value)

  def  wm(self):
    mposstr=pypsepics.get(self.pvrd)
    mpos=double(mposstr)
    return mpos

  def tweak(self,step=0.1,dir=1):
    tweak(self,step=step,dir=dir)
 




  def update_move(self,value,show_previous=True):
    """ moves motor while displaying motor position, CTRL-C stops motor"""
    if (show_previous):
     print "initial position: " + str(self.wm())
    self.move(value)
    sleep(0.02)
    try:
      while(abs(self.wm()-value)>0.005):
        s="motor position: " + str(self.wm())
        utilities.notice(s)
        sleep(0.01)
    except KeyboardInterrupt:
      print "Ctrl-C pressed. trying to stopping motor"
      self.mv(self.wm())
      sleep(1)
    s="motor position: " + str(self.wm())
    utilities.notice(s)




  def umv(self,value):return self.update_move(value)

  def umvr(self,howmuch,show_previous=True):
    startpos=self.wm()
    endpos=startpos+howmuch
    return self.update_move(endpos,show_previous)

  def  wait(self): 
     """ waits until the motor set value equals the readback value, within 10um"""
     while(abs(self.wm() - pypsepics.get(self.pvmv))>0.01): 
       # print "waiting ..."
       sleep(0.02)
