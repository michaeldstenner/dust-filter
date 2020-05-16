#!/usr/bin/env python

import math
import collections

def pcs_to_ugm3(concentration_pcf):
    if isinstance(concentration_pcf, collections.Sequence):
        return [ _pcs_to_ugm3(c) for c in concentration_pcf ]
    else:
        return concentration_pcf

def _pcs_to_ugm3(concentration_pcf):
    """
    Convert concentration of PM2.5 particles per 0.01 cubic feet
    to ug/ metre cubed this method outlined by Drexel University
    students (2009) and is an approximation does not contain
    correction factors for humidity and rain
    """

    if concentration_pcf < 0:
        raise ValueError('Concentration cannot be a negative number')

    # Assume all particles are spherical, with a density of 1.65E12 ug/m3
    densitypm25 = 1.65 * math.pow(10, 12)

    # Assume the radius of a particle in the PM2.5 channel is .44 um
    rpm25 = 0.44 * math.pow(10, -6)

    # Volume of a sphere = 4/3 * pi * radius^3
    volpm25 = (4/3) * math.pi * (rpm25**3)

    # mass = density * volume
    masspm25 = densitypm25 * volpm25

    # parts/m3 =  parts/foot3 * 3531.5
    # ug/m3 = parts/m3 * mass in ug
    concentration_ugm3 = concentration_pcf * 3531.5 * masspm25

    return concentration_ugm3

def ugm3_to_aqi(ugm3):
    if isinstance(ugm3, collections.Sequence):
        return [ _ugm3_to_aqi(c) for c in ugm3 ]
    else:
        return ugm3

def _ugm3_to_aqi(ugm3):
    '''
    Convert concentration of PM2.5 particles in ug/ metre cubed to the USA 
    Environment Agency Air Quality Index - AQI
    https://en.wikipedia.org/wiki/Air_quality_index
    Computing_the_AQI
    https://github.com/intel-iot-devkit/upm/pull/409/commits/ad31559281bb5522511b26309a1ee73cd1fe208a?diff=split
    '''

    bl = [[0.0,   12,    0,   50],
          [12.1,  35.4,  51,  100],
          [35.5,  55.4,  101, 150],
          [55.5,  150.4, 151, 200],
          [150.5, 250.4, 201, 300],
          [250.5, 350.4, 301, 400],
          [350.5, 500.4, 401, 500]]

    C=ugm3
    for b in bl:
        if C <= b[1]:
            return b[2] + (C-b[0]) * ((b[3]-b[2])/(b[1]-b[0]))
    return 500

