# sinks.py
# Jacob Hummel
"""
Classes and routines for analyzing sink data output by gadget.
"""
import sys
import warnings
import numpy as np
import asciitable
import units
#===============================================================================

class SinkData(object):
    def __init__(self,filename):
        super(SinkData,self).__init__()
        ### Read in the data
        try:
            sinkdata = asciitable.read(filename)
        except IOError:
            print "Specified sinkdata file not found!"
            sys.exit()
        self.time = sinkdata['col1']
        self.npart_acc = sinkdata['col2']
        self.radius = sinkdata['col3']
        self.part_internal_energy = sinkdata['col4']
        self.entropy = sinkdata['col5']
        self.part_id = sinkdata['col6']
        self.sink_id  = sinkdata['col7']
        self.pressure = sinkdata['col8']
        self.a = self.time # Scale Facor

        h = 0.7 #Hubble Parameter
        ### Convert units
        self.time = self.time*units.Time_yr
        # npart_acc is a simple integer (no units)
        self.pressure = self.pressure*units.Pressure_cgs*h*h/self.a**5
        self.radius = self.radius*units.Length_AU

class SingleSink(SinkData):
    '''
    Select sink data for a single sink particle.

    possible options:
    nform: select the n(th) sink to form.
    ID: select sink by ID.
    '''
    def __init__(self, filename, nform=None, id_=None):
        super(SingleSink,self).__init__(filename)
        if((nform is None) and (id_ is None)):
            print "No sink specified: Selecting first sink to form..."
            nform = 1
        if nform:
            print "Key set: nform =", nform
            if id_: warnings.warn("nform key overrides id_")
            # Select n(th) sink to form
            new = []
            i = 0
            while len(new) < nform:
                if self.sink_id[i] not in new:
                    new.append(self.sink_id[i])
                i += 1
            print "Unique ID's found:", new
            id_ = new[-1]
        elif id_ is not None:
            print "Key set: id_ =", id_
        else:
            raise RuntimeError("Execution should not have reached this point!")
        print "Using sink ID", id_
        
        # Restrict to a single sink
        lines = np.where(self.sink_id == id_)
        for key in vars(self).keys():
            vars(self)[key] = vars(self)[key][lines]

        # Select final output for each timestep
        tsteps = np.unique(self.time)
        selection = []
        for t in tsteps:
            times = np.where(self.time == t)[0]
            selection.append(times[-1])
        for key in vars(self).keys():
                vars(self)[key] = vars(self)[key][selection]
        self.sink_id = id_
