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

from math import radians, degrees
import pmatic
from sun_position import sun_position

class window(object):
    def __init__(self, name, room_name, shutter_name, ccu, sun):
        self.name = name
        self.room = None
        for room in ccu.rooms:
            if room.name == room_name:
                self.room = room
                break
        if self.room is None:
            print "Error: Invalid room name ", room_name, " in creating window object."
            return
        self.shutter = None
        for device in ccu.devices:
            if shutter_name == device.name:
                self.shutter = device
                break
        if self.shutter is None:
            print "Error: Invalid shutter name ", shutter_name, " in creating window object."
            return
        self.sun = sun
        self.open_spaces = []

    def add_open_space(self, azimuth_lower, azimuth_upper, elevation_lower, elevation_upper):
        self.open_spaces.append([radians(azimuth_lower), radians(azimuth_upper), \
                                 radians(elevation_lower), radians(elevation_upper)])

    def test_sunlit(self):
        sun_azimuth, sun_elevation = self.sun.update_position()
        sunlit = False
        for ([azimuth_lower, azimuth_upper, elevation_lower, elevation_upper]) in self.open_spaces:
            if azimuth_lower <= sun_azimuth <= azimuth_upper and elevation_lower <= sun_elevation <= elevation_upper:
                sunlit = True
                break
        return sunlit

    def set_shutter(self, value):
        if value < 0. or value > 1.:
            print "Error: Invalid shutter value ", value, " specified."
            success = False
        else:
            success = self.shutter.set_value(value)
        return success





if __name__== "__main__":
    ccu = pmatic.CCU(address="http://192.168.0.51", credentials=("Admin", "xxx"), connect_timeout=5)
    longitude = radians(7.9)
    latitude = radians(50.8)
    sun = sun_position(longitude, latitude)

    windows = []

    w = window(u"Küche links", u"Küche", "xxx", ccu, sun)
    w.add_open_space( 50., 120.,  0., 90.)
    w.add_open_space(120., 180., 20., 90.)
    w.add_open_space(180., 220.,  0., 90.)
    windows.append(w)