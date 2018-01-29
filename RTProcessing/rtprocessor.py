""" Signature base class for real-time audio processing

RTProcessor implements a signature class for a simple single-sample processing
unit. Initialize the calss with the sampling rate, the number of channels per
sample (default is 1, i.e. mono audio) and the maximum delay required by the
processing module (e.g. a second order filter will require max_delay=2)

"order" is an attribute that each derived class should redefine to determine
the order of the available classes in an enumeration (useful for user interface)
"""
__author__ = 'Paolo Prandoni'

class RTProcessor(object):
    # position in list of available classes
    order = 1e6     # menu order

    def __init__(self, rate, channels=1, max_delay=1):
        self.SF = rate
        self.x = CircularBuffer(max_delay)
        self.y = CircularBuffer(max_delay)

    def process(self, sample):
        self.x.push(sample)
        y = self._process()
        self.y.push(y)
        return y

    def _process(self):
        # this is the function to "override" for each new processor
        return self.x.get(0)


# As an example, here is a pass-through processor
class Delta(RTProcessor):
    order = 0
    def __init__(self, rate, channels):
        super(Delta, self).__init__(rate, channels)




""" Helper class: circular buffer """
import numpy as np

class CircularBuffer(object):
    def __init__(self, length):
        self.length = length + 1
        self.buf = np.zeros(self.length)
        self.ix = self.length - 1

    def push(self, x):
        self.ix = np.mod(self.ix + 1, self.length)
        self.buf[self.ix] = x

    def get(self, n):
        #print n, np.mod(self.ix + self.length - n, self.length)
        return self.buf[np.mod(self.ix + self.length - n, self.length)]
