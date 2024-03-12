"""
 Copyright (c) 2014 Olivier Le Thanh Duong <olivier@lethanh.be>
This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2,
as published by Sam Hocevar. See the COPYING file for more details.
"""
from datetime import datetime


class PulseCounter(object):

    def __init__(self):
        self.reset()

    def pulse(self, value=None):
        now = datetime.now()
        if not self._start:
            self._start = now
        self.last = now
        self.value = value
        self.n += 1

    @property
    def timedelta(self):
        if self.last != self._start:
            return self.last - self._start
        else:
            return datetime.now() - self._start

    @property
    def speed(self):
        if self.n == 0:
            return 'No pulse'
        pulse_sec = (self.timedelta).total_seconds() / self.n
        if pulse_sec > 0.1:
            t = '%s s/pulse' % (pulse_sec)
        elif pulse_sec * 100 > 0.1:
            t = '%s s/100pulse' % (pulse_sec * 100)
        else:
            t = '%s s/1000pulse' % (pulse_sec * 1000)
        t += ", %s pulse/s" % (self.n / (self.timedelta).total_seconds())
        return t

    def printr(self):
        print '\r', self.value if self.value else "", self.n, ' time', self.timedelta, 'speed:', self.speed,

    def start(self):
        now = datetime.now()
        self.reset()
        self._start = now
        self.last = now

    def stop(self):
        self.stats()
        self.reset()

    def reset(self):
        self.last = None
        self._start = None
        self.n = 0

    def stats(self):
        if self.n <= 2:  # if == 1 display time between start and now, otherwhise between first and last
            print 'Elapsed time', self.timedelta
        else:
            print '\nTotal time: ', self.timedelta, ' Total pulse:', self.n, 'speed:', self.speed

    def pulseprint(self, value=None):
        # pulse & print
        self.pulse(value)
        self.printr()

counter = None


def get_counter_singleton():
    global counter
    if not counter:
        counter = PulseCounter()
    return counter


# FIXME : Find more elegant way to do all of the bellow
def pulse():
    c = get_counter_singleton()
    c.pulse()


def printr():
    c = get_counter_singleton()
    c.printr()


def stats():
    c = get_counter_singleton()
    c.stats()


def start():
    c = get_counter_singleton()
    c.start()


def stop():
    c = get_counter_singleton()
    c.stop()


def pulseprint(value=None):
    c = get_counter_singleton()
    c.pulseprint(value)
