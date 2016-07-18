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

import codecs
import datetime
import sys
import time
from math import radians
from os.path import expanduser, isfile

import pmatic
from sun_position import sun_position


def date_and_time():
    """Compute the current date and time.

    :return: Character string with current date and time information
    """
    return datetime.datetime.fromtimestamp(time.time())


def look_up_device(dev_name):
    """Look up the device by its name

    Args:
        dev_name: device name (utf-8 string)

    Returns: the device object

    """
    try:
        devices = ccu.devices.query(device_name=dev_name)._devices.values()
    except Exception as e:
        print e
    if len(devices) == 1:
        print dev_name
        return devices[0]
    elif len(devices) > 1:
        print date_and_time(), " More than one device with name ", dev_name, " found, first one taken"
    else:
        print date_and_time(), " Error: No device with name ", dev_name, " found, execution halted."
        sys.exit(1)


class window(object):
    def __init__(self, room_name, shutter_name, ccu, sun):
        self.room_name = room_name
        self.shutter_name = shutter_name
        self.shutter = look_up_device(shutter_name)
        self.shutter_last_setting = -1.
        self.shutter_last_set_manually = 0.
        self.shutter_inhibition_time = 7200.
        self.sun = sun
        self.open_spaces = []

    def add_open_space(self, azimuth_lower, azimuth_upper, elevation_lower, elevation_upper):
        self.open_spaces.append([radians(azimuth_lower), radians(azimuth_upper), \
                                 radians(elevation_lower), radians(elevation_upper)])

    def test_sunlit(self):
        sun_azimuth, sun_elevation = self.sun.Look_up_position()
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
            current_time = time.time()
            # Test if current shutter setting differs from target value and no manual intervention is active
            if value != self.shutter.level and current_time - self.shutter_last_set_manually > self.shutter_inhibition_time:
                try:
                    success = self.shutter.set_value(value)
                    self.shutter_last_setting = value
                except Exception as e:
                    print e
                    # Set last setting to impossible value, so deviation will not be interpreted as manual intervention
                    self.shutter_last_setting = -1.
                    success = False
        return success

    def test_manual_intervention(self):
        if self.shutter.level != self.shutter_last_setting and self.shutter_last_setting != -1.:
            self.shutter_last_set_manually = time.time()
            self.shutter_last_setting = self.shutter.level


class windows(object):
    def __init__(self, ccu, sun):
        self.ccu = ccu
        self.sun = sun
        self.window_dict = {}

        # Initialize all windows and set open sky areas
        window_name = u'Küche links'
        w = window(u'Küche', 'xxx', ccu, sun)
        w.add_open_space(50., 120., 0., 90.)
        w.add_open_space(120., 180., 20., 90.)
        w.add_open_space(180., 220., 0., 90.)
        self.window_dict[window_name] = w

    def close_all_shutters(self):
        for window in self.window_dict.values():
            window.set_shutter(0.)

    def open_all_shutters(self):
        for window in self.window_dict.values():
            window.set_shutter(1.)

    def test_manual_intervention(self):
        for window in self.window_dict.values():
            window.test_manual_intervention()


if __name__ == "__main__":
    # Look for config file. If found: read credentials for remote CCU access
    config_file_name = expanduser("~") + "/.pmatic.config"
    if isfile(config_file_name):
        print "Remote execution on PC:"
        file = open(config_file_name, 'r')
        addr, user, passwd = file.read().splitlines()
        print "CCU address: ", addr, ", user: ", user, ", password: ", passwd
        ccu = pmatic.CCU(address=addr, credentials=(user, passwd), connect_timeout=5)
    else:
        print "Local execution on CCU:"
        ccu = pmatic.CCU()
        # For execution on CCU redirect stdout to a protocol file
        sys.stdout = codecs.open('/media/sd-mmcblk0/protocols/shutter_control.txt', encoding='utf-8', mode='a')

    longitude = radians(7.9)
    latitude = radians(50.8)
    sun = sun_position(longitude, latitude)
    sun_twilight_threshold = radians(-5.)

    windows = windows(ccu, sun)

    while True:
        windows.test_manual_intervention()
        sun_azimuth, sun_elevation = sun.update_position()
        if sun_elevation < sun_twilight_threshold:
            windows.close_all_shutters()
        else:
            windows.open_all_shutters()

        time.sleep(120.)
