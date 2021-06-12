#!/usr/bin/env python3
import csv
from datetime import datetime
import math
import io
import logging

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def moving_ave(t, r, N):
    tf = [ t[i]            for i in range(N, len(t)) ]
    rf = [ sum(r[i-N:i])/N for i in range(N, len(t))]
    return (tf, rf)

def exp_smooth(t, r, alpha, beta=0):
    s = [0]
    B = 0
    for v in r[1:]:
        s.append( alpha * v + (1-alpha)*(s[-1] + B) )
        B = beta*(s[-1] - s[-2]) + (1-beta)*B
    return s

def calc_smooth_factor(dt, T):
    return 1 - math.pow(0.5, float(dt)/float(T))

def dtt(t):
    if type(t) in (tuple, list):
        return [ datetime.fromtimestamp(d) for d in t ]
    else:
        return datetime.fromtimestamp(t)

def level_mask(level, v):
    lm = [ l == v for l in level ]
    for i in range(len(level)-1, 0, -1):
        if lm[i-1] is True and lm[i] is False:
            lm[i] = True
    return lm

def mobile_plot(t, level, rr, ra, thresh):
    """generate a mobile plot

    t      = list of unix timestamps
    level  = list of motor level (0-3) (one for each timestamp)
    rr     = list of raw sensor readings (one for each timestamp)
    ra     = list of average sensor readings (one for each timestamp)
    thresh = list of 4 threshold values

    return plot data (bytes object containing a png)
    """

    logging.debug('entering mobile_plot')
    fig, ax = plt.subplots(1)
    logging.debug('setting up figure')
    fig.set_size_inches(4, 2.5)
    fig.patch.set_facecolor((0,0,0))
    ax.set_facecolor((0,0,0))

    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('white')
    #ax.xaxis.label.set_color('red')
    ax.tick_params(axis='x', colors='white')

    ax.spines['left'].set_color('white')
    ax.spines['right'].set_color('white')
    #ax.xaxis.label.set_color('red')
    ax.tick_params(axis='y', colors='white')

    plt.subplots_adjust(left=0.1, bottom=0.15,
                        right=0.99, top=0.99, wspace=0, hspace=0)
    
    rrp = [ r*100.0 for r in rr ]
    rap = [ r*100.0 for r in ra ]
    thp = [ th*100.0 for th in thresh ]
    logging.debug('plotting')
    ax.plot(dtt(t), rrp, 'r', marker='.', linewidth=0.5)
    ax.plot(dtt(t), rap, 'w', marker='.', linewidth=0.5)
    TOP = 1.2 * max( (max(rrp), thp[-1]) )
    ax.fill_between(dtt(t), 0, TOP, where=level_mask(level, 1),
                    facecolor='green', alpha=0.3)
    ax.fill_between(dtt(t), 0, TOP, where=level_mask(level, 2),
                    facecolor='yellow', alpha=0.3)
    ax.fill_between(dtt(t), 0, TOP, where=level_mask(level, 3),
                    facecolor='red', alpha=0.3)
    for th in thp:
        ax.plot(dtt([t[0],t[-1]]), [th, th], 'b', linewidth=0.6)

    plt.xlim(dtt(t[0]), dtt(t[-1]))
    plt.ylim(0, TOP)
    ax.xaxis.set_major_locator(matplotlib.dates.MinuteLocator(interval=1))
    ax.axes.xaxis.set_ticklabels([])
    fo = io.BytesIO()
    logging.debug('saving fig')
    fig.savefig(format='png', fname=fo, transparent=True, dpi=200)
    plt.close()
    fo.seek(0)
    data = fo.read()
    fo.close()
    logging.debug('leaving mobile_plot')
    return data

def _test_data():
    start = 1589722625
    stop = start + 5*60
    rr = []
    ra = []
    t = []
    level = []
    
    from .control import DFControl
    thresh = [0.01, 0.02, 0.04, 0.08]
    dfc = DFControl(thresh)
    import pathlib
    p = pathlib.Path(__file__).parent.joinpath('dustlog.csv')
    with p.open() as csvfile:
        plots = csv.reader(csvfile, delimiter=',')
        for row in plots:
            ti = float(row[0])
            ri = float(row[1])
            li = int(row[2])
            dfc.update(ri, ti)

            if ti < start or ti > stop: continue

            t.append(ti)
            rr.append(ri)
            ra.append(dfc._sv)
            level.append(li)
    return t, level, rr, ra, thresh
    
def plotproc(logq, pipe):
    h = logging.handlers.QueueHandler(logq)
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.DEBUG)
    while True:
        logging.debug('plot proc reading from pipe ...')
        d = pipe.recv()
        logging.debug('plot proc received data from pipe')
        if d is None:
            logging.debug('plot proc exiting')
            break
        logging.debug('plot proc generating plot')
        data = mobile_plot(*d)
        logging.debug('plot proc sending plot data back')
        pipe.send(data)

if __name__ == '__main__':
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    t, level, rr, ra, thresh = _test_data()
    data = mobile_plot(t, level, rr, ra, thresh)
    with open('output.png', 'bw') as fo:
        fo.write(data)
