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
import os.path
from math import radians, degrees

import pmatic
from miscellaneous import *
from parameters import parameters
from sun_position import sun_position


class window(object):
    def __init__(self, params, ccu, sun, window_name, room_name, shutter_name):
        self.params = params
        self.ccu = ccu
        self.sun = sun
        self.window_name = window_name
        self.room_name = room_name
        self.shutter_name = shutter_name
        self.shutter = look_up_device(params, ccu, shutter_name)
        self.shutter_last_setting = -1.
        self.shutter_last_set_manually = 0.
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
        success = True
        if value < 0. or value > 1.:
            print_output("Error: Invalid shutter value " + str(value) + " specified.")
            success = False
        else:
            current_time = time.time()
            # Test if current shutter setting differs from target value and no manual intervention is active
            if value != self.shutter.blind.level and \
                                    current_time - self.shutter_last_set_manually > self.params.shutter_inhibition_time:
                try:
                    if self.params.output_level > 1:
                        print_output("Setting shutter " + self.shutter_name + " to new level: " + str(value))
                    success = self.shutter.blind.set_level(value)
                    time.sleep(params.shutter_trigger_delay)
                    self.shutter_last_setting = value
                except Exception as e:
                    print e
                    # Set last setting to impossible value, so deviation will not be interpreted as manual intervention
                    self.shutter_last_setting = -1.
                    success = False
        return success

    def test_manual_intervention(self):
        if self.shutter.blind.level != self.shutter_last_setting and self.shutter_last_setting != -1.:
            if self.params.output_level > 1:
                print_output("Manual intervention for shutter " + self.shutter_name + " found, new level: "
                             + str(self.shutter.blind.level))
            self.shutter_last_set_manually = time.time()
            self.shutter_last_setting = self.shutter.blind.level


class windows(object):
    def __init__(self, params, ccu, sun):
        self.params = params
        self.ccu = ccu
        self.sun = sun
        self.window_dict = {}

        if self.params.output_level > 0:
            print "\nThe following shutter devices are used:"
        # Initialize all windows and set open sky areas
        window_name = u'Schlafzimmer'
        w = window(self.params, self.ccu, self.sun, window_name, u'Schlafzimmer', u'Rolladenaktor Schlafzimmer')
        w.add_open_space(50., 120., 0., 90.)
        w.add_open_space(120., 180., 20., 90.)
        w.add_open_space(180., 220., 0., 90.)
        self.window_dict[window_name] = w

        if self.params.output_level > 0:
            print "\nWindows with shutter control:"
            for w in self.window_dict.values():
                print "Room: ", w.room_name, ", Window: ", w.window_name, ", Device: ", w.shutter_name

    def close_all_shutters(self):
        if self.params.output_level > 2:
            print_output("Closing all shutters")
        for window in self.window_dict.values():
            window.set_shutter(0.)

    def open_all_shutters(self):
        if self.params.output_level > 2:
            print_output("Opening all shutters")
        for window in self.window_dict.values():
            window.set_shutter(1.)

    def test_manual_intervention(self):
        if self.params.output_level > 2:
            print_output("Testing all shutters for manual intervention")
        for window in self.window_dict.values():
            window.test_manual_intervention()


if __name__ == "__main__":
    ccu_parameter_file_name = "/etc/config/addons/pmatic/scripts/applications/ventilation_basement/parameter_file"
    remote_parameter_file_name = "parameter_file"

    if os.path.isfile(ccu_parameter_file_name):
        params = parameters(ccu_parameter_file_name)
        # For execution on CCU redirect stdout to a protocol file
        sys.stdout = codecs.open('/media/sd-mmcblk0/protocols/shutter_control.txt', encoding='utf-8', mode='a')
        if params.output_level > 0:
            print ""
            print_output(
                "++++++++++++++++++++++++++++++++++ Start Local Execution on CCU +++++++++++++++++++++++++++++++++++++")
        ccu = pmatic.CCU()
    else:
        params = parameters(remote_parameter_file_name)
        if params.output_level > 0:
            print ""
            print_output(
                "++++++++++++++++++++++++++++++++++ Start Remote Execution on PC +++++++++++++++++++++++++++++++++++++")
        ccu = pmatic.CCU(address=params.ccu_address, credentials=(params.user, params.password), connect_timeout=5)

    if params.output_level > 1:
        params.print_parameters()

    sun = sun_position(params)
    sun_twilight_threshold = radians(params.sun_twilight_threshold)

    windows = windows(params, ccu, sun)

    while True:
        if params.update_parameters():
            sun = sun_position(params)
            sun_twilight_threshold = radians(params.sun_twilight_threshold)
            if params.output_level > 1:
                print "\nParameters have changed!"
                params.print_parameters()
        windows.test_manual_intervention()
        sun_azimuth, sun_elevation = sun.update_position()
        if params.output_level > 2:
            print_output("Sun position: Azimuth = " + str(degrees(sun_azimuth)) +
                         ", Elevation = " + str(degrees(sun_elevation)))
        if sun_elevation < sun_twilight_threshold:
            windows.close_all_shutters()
        else:
            windows.open_all_shutters()

        time.sleep(params.main_loop_sleep_time)
