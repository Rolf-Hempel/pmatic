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


class temperature_object(object):
    def __init__(self, params, temperature_device_external):
        self.params = params
        self.temperature_device_external = temperature_device_external
        if os.path.isfile("temperature_file"):
            if self.params.output_level > 1:
                print "File with temperature measurements found, read values"
            with open("temperature_file", "r") as temperature_file:
                self.temp_dict = json.load(temperature_file)
        else:
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

    def update(self):
        current_time = time.time()
        if current_time - self.temp_dict["last_updated"] > self.params.temperature_update_interval:
            try:
                current_temperature_external = self.temperature_device_external.temperature.value
                self.temp_dict["last_updated"] = current_time
                self.temp_dict["temperatures"].append([current_time, current_temperature_external])
                with open("temperature_file", 'w') as temperature_file:
                    json.dump(self.temp_dict, temperature_file)
                if params.output_level > 2:
                    print_output(
                        "External temperature measurement (Celsius) added: " + str(current_temperature_external))
            except Exception as e:
                if self.params.output_level > 0:
                    print e


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

    temperatures = temperature_object(params, temperature_device_external)

    while True:
        temperatures.update()
        time.sleep(params.main_loop_sleep_time)
