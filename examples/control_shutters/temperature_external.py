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

import time

class temperature_external(object):
    def __init__(self, ccu):
        self.devices = ccu.devices.query(device_type=["xxx"])
        self.number_devices = len(self.devices)
        if self.number_devices==0:
            print "Error: No external thermometer found."
        self.temperatures = []
        self.min_temperature = 100.
        self.max_temperature = -100.
        self.update_temperature()

    def update_temperature(self):
        average_temperature = 0.
        for device in self.devices:
            average_temperature += device.temperature
        average_temperature = average_temperature / self.number_devices
        temp_object = [time.time(), average_temperature]
        self.temperatures.append(temp_object)
        for to in self.temperatures:
            pass

    def get_position(self):
        pass


def unix_timestamp_to_julian(unix_secs):
    return ( unix_secs / 86400.0 ) + 2440587.5