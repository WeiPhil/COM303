""" Guitar effects for real-time audio processing

The following classes derived from RTProcessor implement a variety of simple
real-time guitar effects
"""

__author__ = 'Paolo Prandoni'

import numpy as np
from rtprocessor import RTProcessor, Delta


class Echo(RTProcessor):
    """ simple echo, 3 repetition 0.3 seconds apart
    """
    order = 10
    def __init__(self, rate, channels):
        # we will need a second's worth of buffering
        super(Echo, self).__init__(rate, channels, max_delay=rate)

        self.a = 1
        self.b = 0.7
        self.c = 0.5
        self.norm = 1.0 / (self.a + self.b + self.c)
        self.N = int(0.3 * self.SF)


    def _process(self):
         return self.norm * (
             self.a * self.x.get(0) +
             self.b * self.x.get(self.N) +
             self.c * self.x.get(2 * self.N))




class Recursive_Echo(RTProcessor):
    """ Echo implemented as a feedback loop (like Karplus-Strong)
    """
    order = 20
    def __init__(self, rate, channels):
        # we will need a second's worth of buffering
        super(Recursive_Echo, self).__init__(rate, channels, max_delay=rate)

        self.a = 0.7
        self.norm = (1 - self.a * self.a)
        self.N = int(0.3 * self.SF)

    def _process(self):
        # y[n] = x[n] + ay[n-N]
        return self.norm * (self.x.get(0) + self.a * self.y.get(self.N))





class Natural_Echo(RTProcessor):
    """ Echo combining a feedback loop and a simple leaky integrator
    lowpass
    """
    order = 30
    def __init__(self, rate, channels):
        # we will need a second's worth of buffering
        super(Natural_Echo, self).__init__(rate, channels, max_delay=rate)

        self.a = 0.8
        self.l = 0.7
        self.N = int(0.3 * self.SF)

    def _process(self):
        #y [n] = x[n] + y[n-N] * h[n], h[n] leaky integrator
        return self.x.get(0) - self.l * self.x.get(1) + \
                       self.l * self.y.get(1) + self.a * (1-self.l) * self.y.get(self.N)



class Reverb(RTProcessor):
    """ Reverb implemented as a simple first order allpass filter
    """
    order = 40
    def __init__(self, rate, channels):
        super(Reverb, self).__init__(rate, channels, max_delay=rate)

        self.a = 0.8
        self.norm = 0.5
        self.N = int(0.02 * self.SF)

    def _process(self):
        # y[n] = -ax[n] + x[n-N] + ay[n-N]
        return self.norm * (-self.x.get(0) + self.x.get(self.N) + self.a * self.y.get(self.N))




class Biquad(RTProcessor):
    """ Simple second-order filter parametrized in terms of poles
    and zeros
    """
    order = 50
    def __init__(self, rate, channels):
        super(Biquad, self).__init__(rate, channels, max_delay=2)
	    # pole (magnitude and phase)
        pm = 0.98
        pp = 0.1 * np.pi
        # zero (magnitude and phase)
        zm = 0.9
        zp = 0.06 * np.pi

        self.b1 = -2 * zm * np.cos(zp)
        self.b2 = zm * zm
        self.a1 = -2 * pm * np.cos(pp)
        self.a2 = pm * pm

        self.norm = 0.1

    def _process(self):
        # y[n] = x[n] + b_1x[n-1] + b_2x[n-2] - a_1y[n-1] - a_2y[n-2]
        return self.norm * (
            self.x.get(0) + self.b1 * self.x.get(1) + self.b2 * self.x.get(2)
            - self.a1 * self.y.get(1) - self.a2 * self.y.get(2))



class Fuzz(RTProcessor):
    """ Very crude nonlinear limiter (hard distortion)
    """
    order = 60
    def __init__(self, rate, channels):
        # memoryless
        super(Fuzz, self).__init__(rate, channels)

        self.T = 0.005
        self.G = 5

        self.limit = 0x7FFFFFFF * self.T

    def _process(self):
        # y[n] = a trunc(x[n]/a)
        y = self.x.get(0)
        if (y > self.limit):
            y = self.limit
        if (y < -self.limit):
            y = -self.limit
        return self.G*y



class Wah(RTProcessor):
    """ Wah-wah autopedal. A slow oscillator moves the positions of
    the poles in a second-order filter around their nominal value
    The result is a time-varying bandpass filter
    """
    order = 70
    def __init__(self, rate, channels):
        # we just need a second order filter
        super(Wah, self).__init__(rate, channels, max_delay=2)

        self.pole_delta = 0.3 * np.pi            # max pole deviation
        self.phi = 3.0 * 2.0 * np.pi / self.SF   # LFO frequency
        self.omega = 0.0
        self.pole_mag = 0.99                     # pole magnitude
        self.pole_phase = 0.04 * np.pi           # pole phase
        self.zero_mag = 0.9                      # zero magnitude
        self.zero_phase = 0.06 * np.pi           # zero phase

        self.b2 = self.zero_mag * self.zero_mag
        self.a2 = self.pole_mag * self.pole_mag

    def _process(self):
        # current angle of the pole
        d = self.pole_delta * (1.0 + np.cos(self.omega)) / 2.0
        self.omega += self.phi

        # recompute the filter's coefficients
        self.b1 = -2.0 * self.zero_mag * np.cos(self.zero_phase + d)
        self.a1 = -2.0 * self.pole_mag * np.cos(self.pole_phase + d)

        return 0.3 * (self.x.get(0) + self.b1 * self.x.get(1) + self.b2 * self.x.get(2) - \
            self.a1 * self.y.get(1) - self.a2 * self.y.get(2))



class Tremolo(RTProcessor):
    """ In a tremolo, a slow sinusoidal envelope modulates the signal,
    producing a time-varying change in amplitude
    """
    order = 80
    def __init__(self, rate, channels):
        # tremolo is memoryless
        super(Tremolo, self).__init__(rate, channels, max_delay=1)

        self.depth = 0.9
        self.phi = 5 * 2*np.pi / self.SF
        self.omega = 0


    def _process(self):
        self.omega += self.phi;
        return ((1.0 - self.depth) + self.depth * 0.5 * (1 + np.cos(self.omega))) * self.x.get(0)
