#!/usr/bin/env python

try:
    import pigpio
except ImportError:
    print('WARNING: failed to import pigpio')

class Sensor:
    """
    A class to read a Shinyei PPD42NS Dust Sensor, e.g. as used
    in the Grove dust sensor.

    This code calculates the percentage of low pulse time and
    calibrated concentration in particles per 1/100th of a cubic
    foot at user chosen intervals.

    You need to use a voltage divider to cut the sensor output
    voltage to a Pi safe 3.3V (alternatively use an in-line
    20k resistor to limit the current at your own risk).
    """

    def __init__(self, pi, gpio):
        """
        Instantiate with the Pi and gpio to which the sensor
        is connected.
        """

        self.pi = pi
        self.gpio = gpio

        self._state = self.pi.read(gpio)
        self._start_tick = self.pi.get_current_tick() # tick at read
        self._last_tick = self._start_tick # tick at callback
        self._low_ticks = 0
        self._high_ticks = 0

        pi.set_mode(gpio, pigpio.INPUT)

        self._cb = pi.callback(gpio, pigpio.EITHER_EDGE, self._cbf)

    def read(self):
        """
        Calculates the percentage low pulse time and calibrated
        concentration in particles per 1/100th of a cubic foot
        since the last read.

        For proper calibration readings should be made over
        30 second intervals.

        Returns low pulse occupancy ratio
        """
        level = self.pi.read(self.gpio)
        tick = self.pi.get_current_tick()
        self._cbf(self.gpio, level, tick)
        interval = self._low_ticks + self._high_ticks

        if interval > 0:
            ratio = float(self._low_ticks)/float(interval)
        else:
            ratio = 0

        self._start_tick = tick
        self._last_tick = tick
        self._low_ticks = 0
        self._high_ticks = 0

        return ratio

    def read_conc(self):
        ratio = self.read()
        conc = ratio_to_conc(ratio)
        return ratio, conc

    def _cbf(self, gpio, level, tick):
        ticks = pigpio.tickDiff(self._last_tick, tick)
        self._last_tick = tick
        # state is what we have been
        # level is what we are now
        # they may or may not be the same, depending on who called this
        if self._state == 1: # we have been high
            self._high_ticks = self._high_ticks + ticks
        elif self._state == 0: # we have been low
            self._low_ticks = self._low_ticks + ticks
        else: # timeout level, not used
            pass
        #print("%10d %1d %1d" % (ticks, self._state, level))
        self._state = level

def ratio_to_conc(ratio):
    """accepts PPD42NS ratio (not percent) and converts it to
    concentration in particles per 0.01 cubic foot"""
    rp = 100.0 * ratio # ratio as percent
    conc = 1.1*pow(rp,3)-3.8*pow(rp,2)+520*rp
    return conc

if __name__ == "__main__":

   import sys
   import time
   import pigpio
   import PPD42NS

   pi = pigpio.pi() # Connect to Pi.
   s = PPD42NS.Sensor(pi, 25)
   while True:
      time.sleep(5) # Use 30 for a properly calibrated reading.
      r = s.read()
      print('%f,%f' % (time.time(), r))
      sys.stdout.flush()

   pi.stop() # Disconnect from Pi.

