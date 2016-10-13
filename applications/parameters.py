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
import pytz


class parameters(object):
    def __init__(self, parameter_file_name):
        self.parameter_file_name = parameter_file_name
        self.parameters = {}
        self.shutter_condition = {}
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
            if "ow_url_fcst" in self.parameters.keys():
                self.ow_url_fcst = self.parameters["ow_url_fcst"]
            else:
                # Don't forget to set the URL explicitly in the parameter file
                self.ow_url_fcst = ""
            if "max_temp_lookahead_time" in self.parameters.keys():
                self.max_temp_lookahead_time = float(self.parameters["max_temp_lookahead_time"])
            else:
                self.max_temp_lookahead_time = 3.
            if "main_loop_sleep_time" in self.parameters.keys():
                self.main_loop_sleep_time = float(self.parameters["main_loop_sleep_time"])
            else:
                self.main_loop_sleep_time = 71.
            if "lookup_sleep_time" in self.parameters.keys():
                self.lookup_sleep_time = float(self.parameters["lookup_sleep_time"])
            else:
                self.lookup_sleep_time = 5.
            if "temperature_update_interval" in self.parameters.keys():
                self.temperature_update_interval = float(self.parameters["temperature_update_interval"])
            else:
                self.temperature_update_interval = 1800.
            if "brightness_update_interval" in self.parameters.keys():
                self.brightness_update_interval = float(self.parameters["brightness_update_interval"])
            else:
                self.brightness_update_interval = 300.
            if "brightness_time_span" in self.parameters.keys():
                self.brightness_time_span = float(self.parameters["brightness_time_span"])
            else:
                self.brightness_time_span = 3600.
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
            if "lh_night_begin" in self.parameters.keys():
                self.lh_night_begin = float(self.parameters["lh_night_begin"])
            else:
                self.lh_night_begin = 21.
            if "lh_night_end" in self.parameters.keys():
                self.lh_night_end = float(self.parameters["lh_night_end"])
            else:
                self.lh_night_end = 3.943
            if "lh_night_end_saturday" in self.parameters.keys():
                self.lh_night_end_saturday = float(self.parameters["lh_night_end_saturday"])
            else:
                self.lh_night_end_saturday = 4.943
            if "lh_night_end_sunday" in self.parameters.keys():
                self.lh_night_end_sunday = float(self.parameters["lh_night_end_sunday"])
            else:
                self.lh_night_end_sunday = 5.527
            if "min_temperature" in self.parameters.keys():
                self.min_temperature = float(self.parameters["min_temperature"])
            else:
                self.min_temperature = 10.
            if "min_temperature_time" in self.parameters.keys():
                self.min_temperature_time = float(self.parameters["min_temperature_time"])
            else:
                # Set default time stamp of temperature minimum to 3:00 a.m. UTC
                self.min_temperature_time = 10800.
            if "max_temperature" in self.parameters.keys():
                self.max_temperature = float(self.parameters["max_temperature"])
            else:
                self.max_temperature = 20.
            if "max_temperature_very_hot" in self.parameters.keys():
                self.max_temperature_very_hot = float(self.parameters["max_temperature_very_hot"])
            else:
                self.max_temperature_very_hot = 30.
            if "max_temperature_hot" in self.parameters.keys():
                self.max_temperature_hot = float(self.parameters["max_temperature_hot"])
            else:
                self.max_temperature_hot = 25.
            if "max_temperature_cold" in self.parameters.keys():
                self.max_temperature_cold = float(self.parameters["max_temperature_cold"])
            else:
                self.max_temperature_cold = 18.
            if "max_temperature_time" in self.parameters.keys():
                self.max_temperature_time = float(self.parameters["max_temperature_time"])
            else:
                # Set default time stamp of temperature maximum to 11:00 a.m. UTC
                self.max_temperature_time = 39600.
            if "transition_temperature" in self.parameters.keys():
                self.transition_temperature = float(self.parameters["transition_temperature"])
            else:
                self.transition_temperature = 5.
            if "current_temperature_very_hot" in self.parameters.keys():
                self.current_temperature_very_hot = float(self.parameters["current_temperature_very_hot"])
            else:
                self.current_temperature_very_hot = 28.
            if "current_temperature_hot" in self.parameters.keys():
                self.current_temperature_hot = float(self.parameters["current_temperature_hot"])
            else:
                self.current_temperature_hot = 22.
            if "average_humidity_external" in self.parameters.keys():
                self.average_humidity_external = float(self.parameters["average_humidity_external"])
            else:
                self.average_humidity_external = 0.6
            if "brightness_very_bright" in self.parameters.keys():
                self.brightness_very_bright = float(self.parameters["brightness_very_bright"])
            else:
                self.brightness_very_bright = 25000.
            if "brightness_dim" in self.parameters.keys():
                self.brightness_dim = float(self.parameters["brightness_dim"])
            else:
                self.brightness_dim = 7000.
            if "sun_twilight_threshold" in self.parameters.keys():
                self.sun_twilight_threshold = float(self.parameters["sun_twilight_threshold"])
            else:
                self.sun_twilight_threshold = -5.
            if "shutter_trigger_delay" in self.parameters.keys():
                self.shutter_trigger_delay = float(self.parameters["shutter_trigger_delay"])
            else:
                self.shutter_trigger_delay = 40.
            if "shutter_setting_tolerance" in self.parameters.keys():
                self.shutter_setting_tolerance = float(self.parameters["shutter_setting_tolerance"])
            else:
                self.shutter_setting_tolerance = 0.02
            if "max_ventilation_temperature" in self.parameters.keys():
                self.max_ventilation_temperature = float(self.parameters["max_ventilation_temperature"])
            else:
                self.max_ventilation_temperature = 19.

            if "shutter_very-hot-fcst_very-bright_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_very-hot-fcst_very-bright_sunlit"] = float(
                    self.parameters["shutter_very-hot-fcst_very-bright_sunlit"])
            else:
                self.shutter_condition["shutter_very-hot-fcst_very-bright_sunlit"] = 0.18
            if "shutter_very-hot-fcst_very-bright_shade" in self.parameters.keys():
                self.shutter_condition["shutter_very-hot-fcst_very-bright_shade"] = float(
                    self.parameters["shutter_very-hot-fcst_very-bright_shade"])
            else:
                self.shutter_condition["shutter_very-hot-fcst_very-bright_shade"] = 1.00
            if "shutter_very-hot-fcst_normal_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_very-hot-fcst_normal_sunlit"] = float(
                    self.parameters["shutter_very-hot-fcst_normal_sunlit"])
            else:
                self.shutter_condition["shutter_very-hot-fcst_normal_sunlit"] = 0.30
            if "shutter_very-hot-fcst_normal_shade" in self.parameters.keys():
                self.shutter_condition["shutter_very-hot-fcst_normal_shade"] = float(
                    self.parameters["shutter_very-hot-fcst_normal_shade"])
            else:
                self.shutter_condition["shutter_very-hot-fcst_normal_shade"] = 1.00
            if "shutter_very-hot-fcst_dim_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_very-hot-fcst_dim_sunlit"] = float(
                    self.parameters["shutter_very-hot-fcst_dim_sunlit"])
            else:
                self.shutter_condition["shutter_very-hot-fcst_dim_sunlit"] = 0.50
            if "shutter_very-hot-fcst_dim_shade" in self.parameters.keys():
                self.shutter_condition["shutter_very-hot-fcst_dim_shade"] = float(
                    self.parameters["shutter_very-hot-fcst_dim_shade"])
            else:
                self.shutter_condition["shutter_very-hot-fcst_dim_shade"] = 1.00
            if "shutter_hot-fcst_very-bright_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_hot-fcst_very-bright_sunlit"] = float(
                    self.parameters["shutter_hot-fcst_very-bright_sunlit"])
            else:
                self.shutter_condition["shutter_hot-fcst_very-bright_sunlit"] = 0.25
            if "shutter_hot-fcst_very-bright_shade" in self.parameters.keys():
                self.shutter_condition["shutter_hot-fcst_very-bright_shade"] = float(
                    self.parameters["shutter_hot-fcst_very-bright_shade"])
            else:
                self.shutter_condition["shutter_hot-fcst_very-bright_shade"] = 1.00
            if "shutter_hot-fcst_normal_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_hot-fcst_normal_sunlit"] = float(
                    self.parameters["shutter_hot-fcst_normal_sunlit"])
            else:
                self.shutter_condition["shutter_hot-fcst_normal_sunlit"] = 0.40
            if "shutter_hot-fcst_normal_shade" in self.parameters.keys():
                self.shutter_condition["shutter_hot-fcst_normal_shade"] = float(
                    self.parameters["shutter_hot-fcst_normal_shade"])
            else:
                self.shutter_condition["shutter_hot-fcst_normal_shade"] = 1.00
            if "shutter_hot-fcst_dim_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_hot-fcst_dim_sunlit"] = float(
                    self.parameters["shutter_hot-fcst_dim_sunlit"])
            else:
                self.shutter_condition["shutter_hot-fcst_dim_sunlit"] = 0.60
            if "shutter_hot-fcst_dim_shade" in self.parameters.keys():
                self.shutter_condition["shutter_hot-fcst_dim_shade"] = float(
                    self.parameters["shutter_hot-fcst_dim_shade"])
            else:
                self.shutter_condition["shutter_hot-fcst_dim_shade"] = 1.00
            if "shutter_very-hot_very-bright_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_very-hot_very-bright_sunlit"] = float(
                    self.parameters["shutter_very-hot_very-bright_sunlit"])
            else:
                self.shutter_condition["shutter_very-hot_very-bright_sunlit"] = 0.18
            if "shutter_very-hot_very-bright_shade" in self.parameters.keys():
                self.shutter_condition["shutter_very-hot_very-bright_shade"] = float(
                    self.parameters["shutter_very-hot_very-bright_shade"])
            else:
                self.shutter_condition["shutter_very-hot_very-bright_shade"] = 0.50
            if "shutter_very-hot_normal_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_very-hot_normal_sunlit"] = float(
                    self.parameters["shutter_very-hot_normal_sunlit"])
            else:
                self.shutter_condition["shutter_very-hot_normal_sunlit"] = 0.30
            if "shutter_very-hot_normal_shade" in self.parameters.keys():
                self.shutter_condition["shutter_very-hot_normal_shade"] = float(
                    self.parameters["shutter_very-hot_normal_shade"])
            else:
                self.shutter_condition["shutter_very-hot_normal_shade"] = 0.60
            if "shutter_very-hot_dim_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_very-hot_dim_sunlit"] = float(
                    self.parameters["shutter_very-hot_dim_sunlit"])
            else:
                self.shutter_condition["shutter_very-hot_dim_sunlit"] = 0.50
            if "shutter_very-hot_dim_shade" in self.parameters.keys():
                self.shutter_condition["shutter_very-hot_dim_shade"] = float(
                    self.parameters["shutter_very-hot_dim_shade"])
            else:
                self.shutter_condition["shutter_very-hot_dim_shade"] = 0.80
            if "shutter_hot_very-bright_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_hot_very-bright_sunlit"] = float(
                    self.parameters["shutter_hot_very-bright_sunlit"])
            else:
                self.shutter_condition["shutter_hot_very-bright_sunlit"] = 0.25
            if "shutter_hot_very-bright_shade" in self.parameters.keys():
                self.shutter_condition["shutter_hot_very-bright_shade"] = float(
                    self.parameters["shutter_hot_very-bright_shade"])
            else:
                self.shutter_condition["shutter_hot_very-bright_shade"] = 0.60
            if "shutter_hot_normal_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_hot_normal_sunlit"] = float(
                    self.parameters["shutter_hot_normal_sunlit"])
            else:
                self.shutter_condition["shutter_hot_normal_sunlit"] = 0.40
            if "shutter_hot_normal_shade" in self.parameters.keys():
                self.shutter_condition["shutter_hot_normal_shade"] = float(self.parameters["shutter_hot_normal_shade"])
            else:
                self.shutter_condition["shutter_hot_normal_shade"] = 0.80
            if "shutter_hot_dim_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_hot_dim_sunlit"] = float(self.parameters["shutter_hot_dim_sunlit"])
            else:
                self.shutter_condition["shutter_hot_dim_sunlit"] = 0.60
            if "shutter_hot_dim_shade" in self.parameters.keys():
                self.shutter_condition["shutter_hot_dim_shade"] = float(self.parameters["shutter_hot_dim_shade"])
            else:
                self.shutter_condition["shutter_hot_dim_shade"] = 1.00
            if "shutter_normal_very-bright_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_normal_very-bright_sunlit"] = float(
                    self.parameters["shutter_normal_very-bright_sunlit"])
            else:
                self.shutter_condition["shutter_normal_very-bright_sunlit"] = 0.40
            if "shutter_normal_very-bright_shade" in self.parameters.keys():
                self.shutter_condition["shutter_normal_very-bright_shade"] = float(
                    self.parameters["shutter_normal_very-bright_shade"])
            else:
                self.shutter_condition["shutter_normal_very-bright_shade"] = 1.00
            if "shutter_normal_normal_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_normal_normal_sunlit"] = float(
                    self.parameters["shutter_normal_normal_sunlit"])
            else:
                self.shutter_condition["shutter_normal_normal_sunlit"] = 0.60
            if "shutter_normal_normal_shade" in self.parameters.keys():
                self.shutter_condition["shutter_normal_normal_shade"] = float(
                    self.parameters["shutter_normal_normal_shade"])
            else:
                self.shutter_condition["shutter_normal_normal_shade"] = 1.00
            if "shutter_normal_dim_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_normal_dim_sunlit"] = float(
                    self.parameters["shutter_normal_dim_sunlit"])
            else:
                self.shutter_condition["shutter_normal_dim_sunlit"] = 1.00
            if "shutter_normal_dim_shade" in self.parameters.keys():
                self.shutter_condition["shutter_normal_dim_shade"] = float(self.parameters["shutter_normal_dim_shade"])
            else:
                self.shutter_condition["shutter_normal_dim_shade"] = 1.00
            if "shutter_cold_very-bright_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_cold_very-bright_sunlit"] = float(
                    self.parameters["shutter_cold_very-bright_sunlit"])
            else:
                self.shutter_condition["shutter_cold_very-bright_sunlit"] = 1.00
            if "shutter_cold_very-bright_shade" in self.parameters.keys():
                self.shutter_condition["shutter_cold_very-bright_shade"] = float(
                    self.parameters["shutter_cold_very-bright_shade"])
            else:
                self.shutter_condition["shutter_cold_very-bright_shade"] = 1.00
            if "shutter_cold_normal_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_cold_normal_sunlit"] = float(
                    self.parameters["shutter_cold_normal_sunlit"])
            else:
                self.shutter_condition["shutter_cold_normal_sunlit"] = 1.00
            if "shutter_cold_normal_shade" in self.parameters.keys():
                self.shutter_condition["shutter_cold_normal_shade"] = float(
                    self.parameters["shutter_cold_normal_shade"])
            else:
                self.shutter_condition["shutter_cold_normal_shade"] = 1.00
            if "shutter_cold_dim_sunlit" in self.parameters.keys():
                self.shutter_condition["shutter_cold_dim_sunlit"] = float(self.parameters["shutter_cold_dim_sunlit"])
            else:
                self.shutter_condition["shutter_cold_dim_sunlit"] = 1.00
            if "shutter_cold_dim_shade" in self.parameters.keys():
                self.shutter_condition["shutter_cold_dim_shade"] = float(self.parameters["shutter_cold_dim_shade"])
            else:
                self.shutter_condition["shutter_cold_dim_shade"] = 1.00

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
            self.user, "\npassword: ", self.password, \
            "\now_url_fcst: ", self.ow_url_fcst, "\nmax_temp_lookahead_time: ", self.max_temp_lookahead_time, \
            "\nmain_loop_sleep_time: ", self.main_loop_sleep_time, \
            "\nlookup_sleep_time: ", self.lookup_sleep_time, \
            "\ntemperature_update_interval: ", self.temperature_update_interval, \
            "\nbrightness_update_interval: ", self.brightness_update_interval, \
            "\nbrightness_time_span: ", self.brightness_time_span, \
            "\noutput_level: ", self.output_level, "\nlongitude: ", self.longitude, "\nlatitude: ", self.latitude, \
            "\ntimezone: ", self.timezone, \
            "\nlh_night_begin: ", self.lh_night_begin, "\nlh_night_end: ", self.lh_night_end, \
            "\nlh_night_end_saturday: ", self.lh_night_end_saturday, \
            "\nlh_night_end_sunday: ", self.lh_night_end_sunday, \
            "\nmin_temperature: ", self.min_temperature, "\nmin_temperature_time: ", self.min_temperature_time, \
            "\nmax_temperature: ", self.max_temperature, \
            "\nmax_temperature_hot: ", self.max_temperature_hot, \
            "\nmax_temperature_very_hot: ", self.max_temperature_very_hot, \
            "\nmax_temperature_cold: ", self.max_temperature_cold, \
            "\nmax_temperature_time: ", self.max_temperature_time, \
            "\ntransition_temperature: ", self.transition_temperature, \
            "\ncurrent_temperature_very_hot: ", self.current_temperature_very_hot, \
            "\ncurrent_temperature_hot: ", self.current_temperature_hot, \
            "\naverage_humidity_external: ", self.average_humidity_external, \
            "\nbrightness_very_bright: ", self.brightness_very_bright, \
            "\nbrightness_dim: ", self.brightness_dim, \
            "\nsun_twilight_threshold: ", self.sun_twilight_threshold, \
            "\nshutter_trigger_delay: ", self.shutter_trigger_delay, \
            "\nshutter_setting_tolerance: ", self.shutter_setting_tolerance, \
            "\nmax_ventilation_temperature: ", self.max_ventilation_temperature, "\n" \
            "\nshutter_very-hot-fcst_very-bright_sunlit: ", \
            self.shutter_condition["shutter_very-hot-fcst_very-bright_sunlit"], \
            "\nshutter_very-hot-fcst_very-bright_shade: ", self.shutter_condition[
            "shutter_very-hot-fcst_very-bright_shade"], \
            "\nshutter_very-hot-fcst_normal_sunlit: ", self.shutter_condition["shutter_very-hot-fcst_normal_sunlit"], \
            "\nshutter_very-hot-fcst_normal_shade: ", self.shutter_condition["shutter_very-hot-fcst_normal_shade"], \
            "\nshutter_very-hot-fcst_dim_sunlit: ", self.shutter_condition["shutter_very-hot-fcst_dim_sunlit"], \
            "\nshutter_very-hot-fcst_dim_shade: ", self.shutter_condition["shutter_very-hot-fcst_dim_shade"], \
            "\nshutter_hot-fcst_very-bright_sunlit: ", self.shutter_condition["shutter_hot-fcst_very-bright_sunlit"], \
            "\nshutter_hot-fcst_very-bright_shade: ", self.shutter_condition["shutter_hot-fcst_very-bright_shade"], \
            "\nshutter_hot-fcst_normal_sunlit: ", self.shutter_condition["shutter_hot-fcst_normal_sunlit"], \
            "\nshutter_hot-fcst_normal_shade: ", self.shutter_condition["shutter_hot-fcst_normal_shade"], \
            "\nshutter_hot-fcst_dim_sunlit: ", self.shutter_condition["shutter_hot-fcst_dim_sunlit"], \
            "\nshutter_hot-fcst_dim_shade: ", self.shutter_condition["shutter_hot-fcst_dim_shade"], \
            "\nshutter_very-hot_very-bright_sunlit: ", self.shutter_condition["shutter_very-hot_very-bright_sunlit"], \
            "\nshutter_very-hot_very-bright_shade: ", self.shutter_condition["shutter_very-hot_very-bright_shade"], \
            "\nshutter_very-hot_normal_sunlit: ", self.shutter_condition["shutter_very-hot_normal_sunlit"], \
            "\nshutter_very-hot_normal_shade: ", self.shutter_condition["shutter_very-hot_normal_shade"], \
            "\nshutter_very-hot_dim_sunlit: ", self.shutter_condition["shutter_very-hot_dim_sunlit"], \
            "\nshutter_very-hot_dim_shade: ", self.shutter_condition["shutter_very-hot_dim_shade"], \
            "\nshutter_hot_very-bright_sunlit: ", self.shutter_condition["shutter_hot_very-bright_sunlit"], \
            "\nshutter_hot_very-bright_shade: ", self.shutter_condition["shutter_hot_very-bright_shade"], \
            "\nshutter_hot_normal_sunlit: ", self.shutter_condition["shutter_hot_normal_sunlit"], \
            "\nshutter_hot_normal_shade: ", self.shutter_condition["shutter_hot_normal_shade"], \
            "\nshutter_hot_dim_sunlit: ", self.shutter_condition["shutter_hot_dim_sunlit"], \
            "\nshutter_hot_dim_shade: ", self.shutter_condition["shutter_hot_dim_shade"], \
            "\nshutter_normal_very-bright_sunlit: ", self.shutter_condition["shutter_normal_very-bright_sunlit"], \
            "\nshutter_normal_very-bright_shade: ", self.shutter_condition["shutter_normal_very-bright_shade"], \
            "\nshutter_normal_normal_sunlit: ", self.shutter_condition["shutter_normal_normal_sunlit"], \
            "\nshutter_normal_normal_shade: ", self.shutter_condition["shutter_normal_normal_shade"], \
            "\nshutter_normal_dim_sunlit: ", self.shutter_condition["shutter_normal_dim_sunlit"], \
            "\nshutter_normal_dim_shade: ", self.shutter_condition["shutter_normal_dim_shade"], \
            "\nshutter_cold_very-bright_sunlit: ", self.shutter_condition["shutter_cold_very-bright_sunlit"], \
            "\nshutter_cold_very-bright_shade: ", self.shutter_condition["shutter_cold_very-bright_shade"], \
            "\nshutter_cold_normal_sunlit: ", self.shutter_condition["shutter_cold_normal_sunlit"], \
            "\nshutter_cold_normal_shade: ", self.shutter_condition["shutter_cold_normal_shade"], \
            "\nshutter_cold_dim_sunlit: ", self.shutter_condition["shutter_cold_dim_sunlit"], \
            "\nshutter_cold_dim_shade: ", self.shutter_condition["shutter_cold_dim_shade"]


if __name__ == "__main__":
    a = {"hostname": "Vega", "CCU address": "192.168.0.51", "user": "rolf", "output_level": "3"}
    print "Parameters explicitly set in file:", a
    with open("parameter_file", 'w') as f:
        json.dump(a, f)

    params = parameters("parameter_file")

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
