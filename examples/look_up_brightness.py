#!/usr/bin/env python
# encoding: utf-8
#
# pmatic - Python API for Homematic. Easy to use.
# Copyright (C) 2016 Lars Michelsen <lm@larsmichelsen.com>
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

import pmatic

ccu = pmatic.CCU(address="http://192.168.0.51", credentials=("rolf", "Px9820rH"))

for device in ccu.devices.query(device_type=[u"HM-Sen-LI-O"]):
    print device
    print device.channels
    print device.channels[1].values.keys()
    print device.summary_state
    # print "Temperature: ", device.channels[1].values["TEMPERATURE"]
    # print "Humidity: ", device.channels[1].values["HUMIDITY"]

    print "Brightness: ", device.brightness
    print "Battery low: ", device.is_battery_low
    print ""