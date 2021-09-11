# dust-filter
dust filter RPi code

# deps
  - python3-yaml
  - python3-flask
  - python3-matplotlib

# hardware

The hardware build is based on a Raspberry Pi.  It was
built on a Pi 4, but it should run on anything.  The only taxing
operation is the plot generation, and it DOES generate plots all the
time so that a recent plot is available when requested.

The system was built for a JET AFS-1000B Dust Filter.  That system
(and many others) is a three-speed system.  The fan motor has three
taps (in addition to the common) into the motor windings, and applying
high voltage to one of those taps at a time produces three different
fan speeds.  Therefore, three relays can be used to energize one tap
at a time.  I used an Electronics-Salon power relay board; it's a Pi
hat with 3 relays.

For the dust sensor, I used a Shinyei PPD42NS Dust Sensor.  It
required a small amount of electronics, mostly to convert its 5V
signal to 3.3V for the Pi.  For me, this sensor has not held
calibration well, but this has not been a problem.  Basically, I just
adjust my thresholds every 6 months or so.  I *would not* expect this
system (or any system based on this sensor) to provide trustworthy and
reliable calibrated data about the amount of dust.  In my shop, I just
set the lowest threshold a bit above the ambient (clean) dust level.

** Tips

When I modified my JET dust filter, I disconnected the board (there is
a plug) and cut the wires going to it.  I replace the plug with a
standard one, and replace the panel that holds the board.  I can
pretty-easily revert if necessary.

I would recommend wiring in a 5-position rotary switch, where the "hot" can be connected to:
  1. nothing (manual off)
  2. the input to the relays on the Pi relay hat (auto)
  3. the "low" winding directly (manual low)
  4. the "medium" winding directly (manual medium)
  5. the "high" winding directly (manual high)

The software does provide this functionality through the web
interface, but it would be nice to have manual backups.  I did not do
this, but I wish I had.


# test
make test

# run on real hardware (sensors and relays) locally
nohup python3 -m dust_filter.core &

# operation

The basic concept is that there are 3 dust filter states (0=off,
1=low, 2=med, 3=high).  There are 4 settable dust thresholds (0
through 3).  When the 30-second running average of the dust level
*exceeds* threshold N, the state will be increased to state N.  When
the running-average has been *below* threshold N for 5 minutes, the
state will be decreased to state N.  This approach provides fairly
rapid escalation (limited by the 30-second running average), slower
wind-down, and minimizes oscillation between states.

