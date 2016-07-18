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

from os.path import expanduser, isfile

import pmatic

# Look for config file. If found: read credentials for remote CCU access
config_file_name = expanduser("~") + "/.pmatic.config"
if isfile(config_file_name):
    print "Remote execution on PC:"
    file = open(config_file_name, 'r')
    addr, user, passwd = file.read().splitlines()
    print "CCU address: ", addr, ", user: ", user, ", password: ", passwd
    ccu = pmatic.CCU(address=addr, credentials=(user, passwd))
else:
    print "Local execution on CCU:"
    ccu = pmatic.CCU()

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
