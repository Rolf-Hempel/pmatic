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
import math
import sys

import pmatic
from miscellaneous import *
from parameters import parameters


class brightness(object):
    """
    This class measures the external brightness using several measuring devices. The current brightness is set to the
    maximum over all devices. Additionally to the current brightness, the maximum of the measurements over a given
    period up to the present time is determined. This quantity is used by the shutter control program.

    """

    def __init__(self, params, ccu):
        self.params = params
        self.ccu = ccu
        if self.params.output_level > 0:
            print "\nThe following brightness devices will be used:"
        ccu_not_ready_yet = True
        while ccu_not_ready_yet:
            try:
                self.brightness_devices_external = look_up_devices_by_type(params, ccu, u'HM-Sen-LI-O')
                ccu_not_ready_yet = False
            except:
                time.sleep(params.main_loop_sleep_time)
        self.low_battery_found = {}
        for brightness_device in self.brightness_devices_external:
            self.low_battery_found[brightness_device.name] = False
        self.measurement_available = False
        self.brightnesses = []
        self.time_last_updated = 0.
        self.last_brightness_condition = None
        self.last_brightness_change_direction = None

        self.current_time = 0

    def update(self):
        """
        Read out values from brightness measurement devices and update the maximum brightness over a longer time span

        :return: -
        """
        self.current_time = time.time()
        # Do new brightness measurements only if a certain time has passed since the last one
        if self.current_time - self.time_last_updated > self.params.brightness_update_interval:
            # take new brightness measurements
            brightness_measurements = []
            for brightness_device in self.brightness_devices_external:
                try:
                    if brightness_device.is_battery_low:
                        if not self.low_battery_found[brightness_device.name] and self.params.output_level > 0:
                            print_output('*** Warning: Brightness device ' + brightness_device.name +
                                         ' has low battery. ***')
                            self.low_battery_found[brightness_device.name] = True
                    else:
                        brightness_measurements.append(brightness_device.brightness.value)
                        self.low_battery_found[brightness_device.name] = False
                    time.sleep(self.params.lookup_sleep_time)
                except Exception as e:
                    if self.params.output_level > 0:
                        print_error_message(self.ccu, e)
            if len(brightness_measurements) > 0:
                # Set the current brightness to the max over all measuring devices
                self.current_brightness_external = max(brightness_measurements)
                # Add the current measurement together with its time stamp to the list of past readings
                self.brightnesses.append([self.current_time, self.current_brightness_external])
                self.time_last_updated = self.current_time
        # Shorten the list of stored brightness measurements if they span more than the given maximum time span
        first_entry = len(self.brightnesses)
        for i in range(len(self.brightnesses)):
            if self.current_time - self.brightnesses[i][0] <= self.params.brightness_time_span:
                first_entry = i
                break
        self.brightnesses = self.brightnesses[first_entry:]
        self.measurement_available = False
        if len(self.brightnesses) > 0:
            if len(self.brightnesses) == 1:
                self.brightness_external = self.current_brightness_external
            else:
                # self.brightness_external = max([self.brightnesses[j][1] for j in range(len(self.brightnesses))])
                x = []
                y = []
                for i in range(len(self.brightnesses)):
                    x.append(self.brightnesses[i][0]-self.current_time)
                    if self.brightnesses[i][1] > 0.01:
                        y.append(math.log(self.brightnesses[i][1]))
                    else:
                        y.append(-1000.)
                    # y.append(self.brightnesses[i][1])
                a, b = linear_regression(x, y)
                # Evaluate regression function for current_time (i.e. x=0)
                self.brightness_external = math.exp(b)
                # Alternative algorithm: Extrapolate by half the brightness_time_span
                # time_forecast = 0.5 * self.params.brightness_time_span
                # self.brightness_external = max(math.exp(a * time_forecast + b), 0.)
                # self.brightness_external = max(a * time_forecast + b, 0.)
            self.measurement_available = True
            if self.params.output_level > 2:
                print_output("Current external brightness: " + str(self.current_brightness_external) +
                             ", regression value for current time: " + str(self.brightness_external))


    def brightness_condition(self):
        """
        Compare the maximum brightness during the last measurement period with predefined threshold values

        :return: character string which characterizes the current brightness
        """
        if not self.measurement_available:
            return "no_measurement_available"
        elif self.brightness_external > self.params.brightness_very_bright:
            condition = 2
        elif self.brightness_external < self.params.brightness_dim:
            condition = 0
        else:
            condition = 1
        if self.last_brightness_condition is None:
            self.last_brightness_condition = condition
            self.last_brightness_change_time = self.current_time
        elif condition != self.last_brightness_condition:
            change_direction = cmp(condition-self.last_brightness_condition, 0)
            if self.last_brightness_change_direction is None:
                self.last_brightness_change_direction = change_direction
                self.last_brightness_condition = condition
                self.last_brightness_change_time = self.current_time
            elif change_direction == self.last_brightness_change_direction:
                self.last_brightness_condition = condition
                self.last_brightness_change_time = self.current_time
            elif change_direction != self.last_brightness_change_direction and \
                (self.current_time - self.last_brightness_change_time) > self.params.brightness_minimum_reversal_time:
                if condition == 2:
                    margin = self.brightness_external / self.params.brightness_very_bright
                elif condition == 0:
                    margin = self.params.brightness_dim / (self.brightness_external + 0.0001)
                else:
                    if change_direction == 1:
                        margin = self.brightness_external / self.params.brightness_dim
                    else:
                        margin = self.params.brightness_very_bright / (self.brightness_external + 0.0001)
                if margin > self.params.brightness_reversal_margin:
                    self.last_brightness_condition = condition
                    self.last_brightness_change_time = self.current_time
                    self.last_brightness_change_direction = change_direction
                else:
                    condition = self.last_brightness_condition
            else:
                condition = self.last_brightness_condition
        if condition == 0:
            return "dim"
        elif condition == 1:
            return "normal"
        else:
            return "very-bright"



if __name__ == "__main__":
    # Depending on whether the program is executed on the CCU2 itself or on a remote PC, the parameters are stored at
    # different locations.
    ccu_parameter_file_name = "/etc/config/addons/pmatic/scripts/applications/parameter_file"
    remote_parameter_file_name = "parameter_file"

    if os.path.isfile(ccu_parameter_file_name):
        params = parameters(ccu_parameter_file_name)
        # For execution on CCU redirect stdout to a protocol file
        sys.stdout = codecs.open('/media/sd-mmcblk0/protocols/brightness.txt', encoding='utf-8', mode='a')
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

    brightness_measurements = brightness(params, ccu)

    while True:
        brightness_measurements.update()
        if params.output_level > 2:
            print "brightness condition: ", brightness_measurements.brightness_condition()
        time.sleep(params.main_loop_sleep_time)
