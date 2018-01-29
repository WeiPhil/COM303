""" Demo program showing how to process audio in real time using Python.
Requires PortAudio and pyaudio.
"""

__author__ = 'Paolo Prandoni'

import pyaudio
import time
import os
import numpy as np
if os.name == 'nt':
    WINDOWS = True
    import msvcrt
else:
    import select
import inspect
import sys


# audio format
RATE = 16000
CHANNELS = 1

# number of buffers in pipe. reduce for lower latency
DELAY = 5

# the module containing the processing classes
PROCESSING_MODULE = "guitar_effects"


def poll_keyboard():
    # check for key presses in a platform-independent way
    global WINDOWS
    if WINDOWS:
        key = ord(msvcrt.getch()) if msvcrt.kbhit() else 0
    else:
        key, _, _ = select.select([sys.stdin], [], [], 0)
    return key



def print_choices(choices, key):
    # print available processing choices
    print '\n\nnow using processor ', choices[key]
    print "available choices:"
    for ix in choices:
        print ix, ') ', choices[ix]



def main():
    # scan available processing modules and build a list
    processing_module = __import__(PROCESSING_MODULE)
    p = inspect.getmembers(sys.modules[PROCESSING_MODULE], inspect.isclass)
    p = [(e[1].order, e[0]) for e in p if e[1].__module__ == PROCESSING_MODULE]
    p = sorted(p)
    # add the default class
    choices = {0: "Delta"}
    for ix, c in enumerate(p):
        choices[ix+1] = c[1]

    # callback function for the audio pipe. Process data and return
    # the proc variable is user-updated in the main loop
    def callback(in_data, frame_count, time_info, status):
        audio_data = np.fromstring(in_data, dtype=np.int32)
        for n in range(0, len(audio_data)):
            audio_data[n] = np.int32(processor.process(audio_data[n]))
        return (audio_data, pyaudio.paContinue)

    # instantiate pyaudio
    pa = pyaudio.PyAudio()
    # open a bidirectional stream; a "frame" is a set of concurrent
    # samples (2 for stereo, 1 for mono) so the frames_per_buffer param
    # gives the size of the input and output buffers
    stream = pa.open(
        format=pyaudio.paInt32,
        channels=CHANNELS,
        rate=RATE,
            frames_per_buffer=1,
        input=True,
        output=True,
        stream_callback=callback)

    print "\nstarting audio processing"
    print "press Q at any time to quit\n"

    # default processing module is the "no processing"
    key = 0
    processor = getattr(processing_module, choices[key])(RATE, CHANNELS)
    print_choices(choices, key)

    # start recording and playing
    stream.start_stream()
    while stream.is_active():
        key = poll_keyboard()
        if key == ord('q'):
            break
        else:
            key = key - ord('0')
            try:
                processor = getattr(processing_module, choices[key])(RATE, CHANNELS)
                print_choices(choices, key)
            except KeyError:
                pass
        time.sleep(0.1)

    stream.stop_stream()
    stream.close()
    pa.terminate()



if __name__ == '__main__':
    main()

