from datetime import timedelta

import math

class Timestamp(object):
    def __init__(self, total_milliseconds):
        self.total_milliseconds = total_milliseconds

    def map(self, f):
        return Timestamp(f(self.total_milliseconds))

    def floor(self):
        return self.map(math.floor)

    def ceil(self):
        return self.map(math.ceil)

    @property
    def total_seconds(self):
        return self.total_milliseconds / 1000

    @staticmethod
    def from_s(string):
        while len(string) < len("HH:MM:SS.sss"):
            string += "0"

        hours = int(string[:2])
        minutes = int(string[3:5])
        seconds = int(string[6:8])
        milliseconds = int(string[9:])
        return Timestamp((hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds)

    @staticmethod
    def from_timedelta(delta : timedelta):
        return Timestamp(delta.total_seconds() * 1000)

    def __add__(self, other):
        assert isinstance(other, type(self))
        return Timestamp(self.total_milliseconds + other.total_milliseconds)

    def __sub__(self, other):
        assert isinstance(other, type(self))
        return Timestamp(self.total_milliseconds - other.total_milliseconds)

    def __eq__(self, other):
        assert isinstance(other, type(self))
        return self.total_milliseconds == other.total_milliseconds

    def __lt__(self, other):
        assert isinstance(other, type(self))
        return self.total_milliseconds < other.total_milliseconds

    def __gt__(self, other):
        assert isinstance(other, type(self))
        return self.total_milliseconds > other.total_milliseconds

    def __str__(self):
        milliseconds = self.total_milliseconds % 1000

        remaining_seconds = self.total_milliseconds // 1000
        seconds = remaining_seconds % 60

        remaining_minutes = remaining_seconds // 60
        minutes = remaining_minutes % 60

        hours = remaining_minutes // 60

        return "%02d:%02d:%02d.%03d" % (hours, minutes, seconds, milliseconds)

    def __repr__(self):
        return self.__str__()
