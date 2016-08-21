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

    def __init__(self, params, ccu, temperature_file_name):
        self.params = params
        self.temperature_file_name = temperature_file_name

        if self.params.output_level > 0:
            print "\nThe following temperature device will be used:"
        self.temperature_device_external = look_up_device_by_name(params, ccu, u'Temperatur- und Feuchtesensor außen')

        # Check if a file with previously written temperature information is available
        if os.path.isfile(self.temperature_file_name):
            if self.params.output_level > 1:
                print "File with temperature measurements found, read values"
            with open(self.temperature_file_name, "r") as temperature_file:
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
            with open(self.temperature_file_name, 'w') as temperature_file:
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

                # Update minima / maxima data at the first invocation after 18:00 local time,
                # but only if data have been recorded for at least 18 hours
                if current_time - self.temp_dict["minmax_time_updated"] > 64800. and 18. < local_hour < 24.:
                    if self.params.output_level > 1:
                        print_output(
                            "\nUpdating maximum and minimum external temperatures:")
                    min_temperature = 100.
                    max_temperature = -100.
                    for temp_object_stored in self.temp_dict["temperatures"]:
                        local_hour = get_local_hour(self.params, temp_object_stored[0])
                        # Look for maximum temperature only between 1:00 and 6:00 p.m. local time
                        if 13. < local_hour < 18. and temp_object_stored[1] > max_temperature:
                            max_temperature = temp_object_stored[1]
                            max_temperature_time = temp_object_stored[0]
                        # Look for minimum temperature only between 3:00 and 9:00 a.m. local time
                        if 3. < local_hour < 9. and temp_object_stored[1] < min_temperature:
                            min_temperature = temp_object_stored[1]
                            min_temperature_time = temp_object_stored[0]
                    if max_temperature == -100. and min_temperature == 100. and self.params.output_level > 1:
                        print "No new maximum or minimum temperature found"
                    else:
                        if max_temperature > -100.:
                            if self.params.output_level > 1:
                                print "New maximum temperature: " + str(max_temperature) + ", Time of maximum: " + str(
                                    datetime.datetime.fromtimestamp(max_temperature_time))
                            self.temp_dict["max_temperature"] = max_temperature
                            self.temp_dict["max_temperature_time"] = max_temperature_time
                        if min_temperature < 100.:
                            if self.params.output_level > 1:
                                print "New minimum temperature: " + str(min_temperature) + ", Time of minimum: " + str(
                                    datetime.datetime.fromtimestamp(min_temperature_time))

                    self.temp_dict["minmax_time_updated"] = current_time
                    self.temp_dict["temperatures"] = [temp_object]
                else:
                    self.temp_dict["temperatures"].append(temp_object)
                with open(self.temperature_file_name, 'w') as temperature_file:
                    json.dump(self.temp_dict, temperature_file)
            except Exception as e:
                if self.params.output_level > 0:
                    print e
            time.sleep(self.params.lookup_sleep_time)

    def temperature_condition(self):
        """
        Compare the current and maximum temperatures with predefined threshold values. For the characterization "hot"
        both the current temperature and the maximum temperature of the previous day are used.

        :return: character string which characterizes the current temperature situation
        """
        if self.current_temperature_external > self.params.current_temperature_hot or self.temp_dict[
            "max_temperature"] > self.params.max_temperature_hot:
            return "hot"
        elif self.temp_dict["max_temperature"] < self.params.max_temperature_cold:
            return "cold"
        else:
            return "normal"


if __name__ == "__main__":
    # Depending on whether the program is executed on the CCU2 itself or on a remote PC, the parameters are stored at
    # different locations.
    ccu_parameter_file_name = "/etc/config/addons/pmatic/scripts/applications/parameter_file"
    remote_parameter_file_name = "parameter_file"
    ccu_temperature_file_name = "/etc/config/addons/pmatic/scripts/applications/temperature_file"
    remote_temperature_file_name = "temperature_file"

    if os.path.isfile(ccu_parameter_file_name):
        params = parameters(ccu_parameter_file_name)
        temperature_file_name = ccu_temperature_file_name
        # For execution on CCU redirect stdout to a protocol file
        sys.stdout = codecs.open('/media/sd-mmcblk0/protocols/temperature.txt', encoding='utf-8', mode='a')
        if params.output_level > 0:
            print ""
            print_output(
                "++++++++++++++++++++++++++++++++++ Start Local Execution on CCU +++++++++++++++++++++++++++++++++++++")
        ccu = pmatic.CCU()
    else:
        params = parameters(remote_parameter_file_name)
        temperature_file_name = remote_temperature_file_name
        if params.output_level > 0:
            print ""
            print_output(
                "++++++++++++++++++++++++++++++++++ Start Remote Execution on PC +++++++++++++++++++++++++++++++++++++")
        ccu = pmatic.CCU(address=params.ccu_address, credentials=(params.user, params.password), connect_timeout=5)

    if params.output_level > 1:
        params.print_parameters()

    temperatures = temperature(params, ccu, temperature_file_name)

    while True:
        temperatures.update()
        if params.output_level > 2:
            print "temperature condition: ", temperatures.temperature_condition()
        time.sleep(params.main_loop_sleep_time)
