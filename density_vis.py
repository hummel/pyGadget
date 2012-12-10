#!/usr/bin/env python
# density_vis.py
# Jacob Hummel

import os
import sys
import glob
import numpy
import Queue
from matplotlib import pyplot
from matplotlib import cm
from matplotlib.mlab import griddata
import pp

import pyGadget
import statistics

#===============================================================================
def load_dens(fname,length_unit):
    snapshot = pyGadget.snapshot.File(fname)
    particle_mass = snapshot.gas.load_masses()
    dens = snapshot.gas.load_number_density()
    pos = snapshot.gas.load_coords(length_unit)
    smL = snapshot.gas.load_smoothing_length(length_unit)
    sinkval = snapshot.gas.load_sinks()
    return snapshot

def plot_dens(snap, write_dir, job_server, 
              boxsize, length_unit, pps, hsml_factor):
    for suffix in ['-dens-xy.png','-dens-xz.png','-dens-yz.png']:
        wpath = write_dir + '{:0>4}'.format(snap.number) + suffix
        view = suffix[-6:-4]
        x,y,z = pyGadget.visualize.density(snap, view, boxsize, 1., 
                                           length_unit, job_server, 
                                           pps, hsml_factor)
        z = numpy.log10(z)
        zmin,zmax = (1e9,7e11)
        
        print 'Plotting '+view+'...'
        fig = pyplot.figure(1,(12,12))
        fig.clf()
        pyplot.imshow(z, extent=[x.min(),x.max(),y.min(),y.max()],
                      cmap=cm.jet)
        pyplot.clim(numpy.log10(zmin),numpy.log10(zmax))
        ax = pyplot.gca()
        for sink in snap.sinks:
            ax.plot(sink[1], -sink[0], 'ko') # 90-degree rotation
        ax.set_xlim(x.min(),x.max())
        ax.set_ylim(y.min(),y.max())
        ax.set_xlabel('AU')
        ax.set_ylabel('AU')
        ax.set_title('Redshift: %.7f' %snap.header.Redshift)
        pyplot.draw()
        pyplot.savefig(wpath, 
                       bbox_inches='tight')
    snap.close()

def multitask(path, write_dir, start, stop,
              boxsize,length_unit,pps,hsml_factor):
    job_server = pp.Server()
    file_queue = Queue.Queue()
    data_queue = Queue.Queue(3)
    pyGadget.snapshot.Loader(load_dens, file_queue, data_queue).start()
    # Add filenames to the queue
    for i in xrange(start,stop+1):
        fname = path + '{:0>3}'.format(i) + '.hdf5'
        file_queue.put((fname,length_unit))
    file_queue.put(None)
    # Process images
    while 1:
        snapshot = data_queue.get()
        if snapshot is None:
            break # reached end of queue!
        plot_dens(snapshot,write_dir,job_server,
                  boxsize,length_unit,pps,hsml_factor)
    job_server.destroy()
    print 'Done.'
    
#===============================================================================
pyplot.ioff()
if ((len(sys.argv) not in [2,3,4]) or (sys.argv[1] == '-h')):
    print 'Usage::'
    print '   Option 1: python gas_temp.py [simulation name] '\
        '[beginning snapshot] [final snapshot]'
    print '   Option 2: python gas_temp.py [simulation name] '\
        '[single snapshot]'
    print '   Option 3: python gas_temp.py [simulation name] '\
        '(creates a plot for every snapshot)'
    sys.exit()

simulation = sys.argv[1]
path = os.getenv('HOME')+'/sim/'+simulation+'/snapshot_'
write_dir = os.getenv('HOME')+'/data/simplots/'+simulation+'/'

length_unit = pyGadget.units.Length_AU
pps = 1000 # 'pixels' per side
hsml_factor = 1.5
boxsize = 2e3

if len(sys.argv) == 3:
    snap = sys.argv[2]
    fname = path + '{:0>3}'.format(snap)+'.hdf5'
    print 'loading', fname
    snapshot = load_dens(fname,length_unit)
    js = pp.Server()
    plot_dens(snapshot,write_dir,js,boxsize,length_unit,pps,hsml_factor)
    js.destroy()

elif len(sys.argv) == 4:
    start = int(sys.argv[2])
    stop = int(sys.argv[3])+1
    multitask(path,write_dir,start,stop,
              boxsize,length_unit,pps,hsml_factor)

else:
    files0 = glob.glob(path+'???.hdf5')
    files1 = glob.glob(path+'1???.hdf5')
    files0.sort()
    files1.sort()
    start = int(files0[0][:-5])
    stop = int(files0[-1][-8:-5])
    if files1:
        stop = int(files1[-1][-9:-5])
        
    multitask(path,write_dir,start,stop,
              boxsize,length_unit,pps,hsml_factor)
