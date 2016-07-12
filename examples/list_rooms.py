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

for room in ccu.rooms:
    print("%-30s %d devices" % (room.name, len(room.devices)))
    for device in room.devices:
        state = device.summary_state
        print device.name, ", ", device.type, ", ", device.summary_state

devices = ccu.devices.query(device_name=u'Temperatur- und Feuchtesensor außen')
for device in devices:
    print len(devices), device.name, device.summary_state
