#!/usr/bin/env python
# encoding: utf-8
#
# Application code for pmatic - Python API for Homematic. Easy to use.
# Copyright (C) 2016 Rolf Hempel <rolf6419@gmx.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from math import degrees, radians

from parameters import parameters
from pmatic import utils


class sun_position(object):
    def __init__(self, params):
        self.longitude = radians(params.longitude)
        self.latitude = radians(params.latitude)
        self.update_position

    def update_position(self):
        self.azimuth, self.elevation = utils.sun_position(self.longitude, self.latitude)
        return self.azimuth, self.elevation

    def look_up_position(self):
        return self.azimuth, self.elevation


if __name__ == "__main__":
    params = parameters()
    sun = sun_position(params)
    azimuth, elevation = sun.update_position()

    print "Azimuth: ", degrees(azimuth), ", Elevation: ", degrees(elevation)