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

import json


class parameters(object):
    def __init__(self, parameter_file_name):
        self.parameter_file_name = parameter_file_name
        self.parameters = {}
        self.update_parameters()

    def update_parameters(self):
        self.parameters_old = self.parameters
        with open(self.parameter_file_name, "r") as parameter_file:
            self.parameters = json.load(parameter_file)
        if self.test_for_changes():
            if "hostname" in self.parameters.keys():
                self.hostname = self.parameters["hostname"]
            else:
                self.hostname = "homematic-ccu2"
            if "ccu_address" in self.parameters.keys():
                self.ccu_address = self.parameters["ccu_address"]
            else:
                self.ccu_address = "192.168.0.51"
            if "user" in self.parameters.keys():
                self.user = self.parameters["user"]
            else:
                self.user = "rolf"
            if "password" in self.parameters.keys():
                self.password = self.parameters["password"]
            else:
                # Don't forget to set the password explicitly in the parameter file
                self.password = ""
            if "main_loop_sleep_time" in self.parameters.keys():
                self.main_loop_sleep_time = float(self.parameters["main_loop_sleep_time"])
            else:
                self.main_loop_sleep_time = 121.
            if "output_level" in self.parameters.keys():
                self.output_level = int(self.parameters["output_level"])
            else:
                self.output_level = 1
            if "longitude" in self.parameters.keys():
                self.longitude = float(self.parameters["longitude"])
            else:
                self.longitude = 7.9
            self.utc_shift = self.longitude / 15.
            if "latitude" in self.parameters.keys():
                self.latitude = float(self.parameters["latitude"])
            else:
                self.latitude = 50.7
            if "min_temperature" in self.parameters.keys():
                self.min_temperature = float(self.parameters["min_temperature"])
            else:
                self.min_temperature = 5.
            if "min_temperature_time" in self.parameters.keys():
                self.min_temperature_time = float(self.parameters["min_temperature_time"])
            else:
                # Set default time stamp of temperature minimum to 3:00 a.m. UTC
                self.min_temperature_time = 10800.
            if "max_temperature" in self.parameters.keys():
                self.max_temperature = float(self.parameters["max_temperature"])
            else:
                self.max_temperature = 10.
            if "max_temperature_time" in self.parameters.keys():
                self.max_temperature_time = float(self.parameters["max_temperature_time"])
            else:
                # Set default time stamp of temperature maximum to 11:00 a.m. UTC
                self.max_temperature_time = 39600.
            if "transition_temperature" in self.parameters.keys():
                self.transition_temperature = float(self.parameters["transition_temperature"])
            else:
                self.transition_temperature = 5.
            if "average_humidity_external" in self.parameters.keys():
                self.average_humidity_external = float(self.parameters["average_humidity_external"])
            else:
                self.average_humidity_external = 0.6
            if "sun_twilight_threshold" in self.parameters.keys():
                self.sun_twilight_threshold = float(self.parameters["sun_twilight_threshold"])
            else:
                self.sun_twilight_threshold = -1.
            if "shutter_trigger_delay" in self.parameters.keys():
                self.shutter_trigger_delay = float(self.parameters["shutter_trigger_delay"])
            else:
                self.shutter_trigger_delay = 40.
            if "max_ventilation_temperature" in self.parameters.keys():
                self.max_ventilation_temperature = float(self.parameters["max_ventilation_temperature"])
            else:
                self.max_ventilation_temperature = 19.
            return True
        else:
            return False

    def test_for_changes(self):
        set_1 = set(self.parameters.iteritems())
        set_2 = set(self.parameters_old.iteritems())
        len(set_1.difference(set_2))
        return (len(set_1.difference(set_2)) | len(set_2.difference(set_1)))

    def print_parameters(self):
        print "\nParameters:", "\nhostname: ", self.hostname, "\nCCU address: ", self.ccu_address, "\nuser: ", \
            self.user, "\npassword: ", self.password, "\nmain_loop_sleep_time: ", self.main_loop_sleep_time, \
            "\noutput_level: ", self.output_level, "\nlongitude: ", self.longitude, "\nlatitude: ", self.latitude, \
            "\nmin_temperature: ", self.min_temperature, "\nmin_temperature_time: ", self.min_temperature_time, \
            "\nmax_temperature: ", self.max_temperature, "\nmax_temperature_time: ", self.max_temperature_time, \
            "\ntransition_temperature: ", self.transition_temperature, \
            "\naverage_humidity_external: ", self.average_humidity_external, \
            "\nsun_twilight_threshold: ", self.sun_twilight_threshold, \
            "\nshutter_inhibition_time: ", self.shutter_inhibition_time, \
            "\nshutter_trigger_delay: ", self.shutter_trigger_delay


if __name__ == "__main__":
    a = {"hostname": "Vega", "CCU address": "192.168.0.51", "user": "rolf", "output_level": "3"}
    print "Parameters explicitly set in file:", a
    with open("parameter_file", 'w') as f:
        json.dump(a, f)

    params = parameters()

    params.print_parameters()

    a = {"hostname": "Vega", "CCU address": "192.168.0.51", "user": "rolf", "output_level": "3"}
    print "\nParameters explicitly set in file:", a
    with open("parameter_file", 'w') as f:
        json.dump(a, f)

    if params.update_parameters():
        print "\nParameters have changed!"
        params.print_parameters()
    else:
        print "\nParameters are identical!"
