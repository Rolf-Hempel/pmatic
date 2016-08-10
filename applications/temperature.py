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
import json
import os.path

import pmatic
from miscellaneous import *
from parameters import parameters


class temperature(object):
    """
    This class keeps a persistent list of temperature measurements and statistical values on temperature minima and
    maxima. When a new measurement is available, the statistics are updated and the new data are stored in a file.
    After a program interruption, the file is read on program restart.

    """

    def __init__(self, params, temperature_device_external):
        self.params = params
        self.temperature_device_external = temperature_device_external
        # Check if a file with previously written temperature information is available
        if os.path.isfile("temperature_file"):
            if self.params.output_level > 1:
                print "File with temperature measurements found, read values"
            with open("temperature_file", "r") as temperature_file:
                self.temp_dict = json.load(temperature_file)
        else:
            # No previously stored data available, initialize a new temperature dictionary
            if self.params.output_level > 1:
                print "No file with temperature measurements found, initialize temperature_object and create file"
            self.temp_dict = {}
            self.temp_dict["temperatures"] = []
            self.temp_dict["last_updated"] = 0.
            self.temp_dict["minmax_time_updated"] = 0.
            self.temp_dict["min_temperature"] = params.min_temperature
            self.temp_dict["min_temperature_time"] = params.min_temperature_time
            self.temp_dict["max_temperature"] = params.max_temperature
            self.temp_dict["max_temperature_time"] = params.max_temperature_time
            with open("temperatures", 'w') as temperature_file:
                json.dump(self.temp_dict, temperature_file)
        self.current_temperature_external = (self.temp_dict["min_temperature"] + self.temp_dict["max_temperature"]) / 2.

    def update(self):
        # Do a new temperature measurement and update the temperature statistics
        current_time = time.time()
        local_hour = get_local_hour(self.params, current_time)
        if current_time - self.temp_dict["last_updated"] > self.params.temperature_update_interval:
            try:
                self.current_temperature_external = self.temperature_device_external.temperature.value
                if self.params.output_level > 2:
                    print_output("External temperature: " + str(self.current_temperature_external))
                temp_object = [current_time, self.current_temperature_external]
                self.temp_dict["last_updated"] = current_time

                # Update minima / maxima data at the first invocation after 12:00 a.m. local time,
                # but only if data have been recorded at least since 01:00 p.m. on previous day
                if current_time - self.temp_dict["minmax_time_updated"] > 82800. and 12. < local_hour < 13.:
                    self.temp_dict["min_temperature"] = 100.
                    self.temp_dict["max_temperature"] = -100.
                    for to in self.temp_dict["temperatures"]:
                        local_hour = get_local_hour(self.params, to[0])
                        # Look for maximum temperature only between 1:00 and 6:00 p.m. local time
                        if to[1] > self.temp_dict["max_temperature"] and 13. < local_hour < 18.:
                            self.temp_dict["max_temperature"] = to[1]
                            self.temp_dict["max_temperature_time"] = to[0]
                        # Look for minimum temperature only between 3:00 and 9:00 a.m. local time
                        if to[1] < self.temp_dict["min_temperature"] and 3. < local_hour < 9.:
                            self.temp_dict["min_temperature"] = to[1]
                            self.temp_dict["min_temperature_time"] = to[0]
                    if self.params.output_level > 1:
                        print ""
                        print_output(
                            " Updating maximum and minimum external temperatures:\nNew maximum temperature: " + str(
                                self.temp_dict["max_temperature"]) + ", Time of maximum: " + str(
                                datetime.datetime.fromtimestamp(
                                    self.temp_dict["max_temperature_time"])) + " \nNew minimum temperature: " + str(
                                self.temp_dict["min_temperature"]) + ", Time of minimum: " + str(
                                datetime.datetime.fromtimestamp(
                                    self.temp_dict["min_temperature_time"])))

                        self.temp_dict["minmax_time_updated"] = current_time
                        self.temp_dict["temperatures"] = [temp_object]
                else:
                    self.temp_dict["temperatures"].append(temp_object)
                with open("temperature_file", 'w') as temperature_file:
                    json.dump(self.temp_dict, temperature_file)
            except Exception as e:
                if self.params.output_level > 0:
                    print e
            time.sleep(params.lookup_sleep_time)

    def temperature_condition(self):
        if self.current_temperature_external > params.current_temperature_hot or self.temp_dict[
            "max_temperature"] > params.max_temperature_hot:
            return "hot"
        elif self.temp_dict["max_temperature"] < params.max_temperature_cold:
            return "cold"
        else:
            return "normal"


if __name__ == "__main__":
    # Depending on whether the program is executed on the CCU2 itself or on a remote PC, the parameters are stored at
    # different locations.
    ccu_parameter_file_name = "/etc/config/addons/pmatic/scripts/applications/parameter_file"
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

    print "\nThe following temperature device will be used:"
    temperature_device_external = look_up_device(params, ccu, u'Temperatur- und Feuchtesensor außen')

    temperatures = temperature(params, temperature_device_external)

    while True:
        temperatures.update()
        if params.output_level > 2:
            print "temperature condition: ", temperatures.temperature_condition()
        time.sleep(params.main_loop_sleep_time)
