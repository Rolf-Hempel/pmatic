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

# Trigger a short button press for the first button of a HM-PBI-4-FM device
# for device in ccu.devices.query(device_name=u"Büro-Schalter"):
#     if device.switch1.press_short():
#         print("done.")
#     else:
#         print("failed!")

# for device in ccu.devices.query(device_type=u"HM-LC-Sw1-Pl-DN-R1"):
#     # print device
#     # print device.channels
#     # print device.channels[1]
#     # print device.summary_state

device = ccu.devices.query(device_name=u"Steckdosenschalter Gartenkeller")._devices.values()[0]
print "Name of switch device: ", device.name
try:
    device.switch_on()
except Exception as e:
    print e
print "Switch device is on: ", device.is_on
device.switch_off()
print "Switch device is on: ", device.is_on
print device.switch.summary_state
