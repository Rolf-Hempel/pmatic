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
import sys
import urllib2
from math import floor

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
            print "\nThe following external temperature device will be used:"
        ccu_not_ready_yet = True
        while ccu_not_ready_yet:
            try:
                self.temperature_device_external = look_up_device_by_name(params, ccu,
                                                                          u'Temperatur- und Feuchtesensor außen')
                ccu_not_ready_yet = False
            except:
                time.sleep(params.main_loop_sleep_time)

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
            self.temp_dict["temperatures_forecast"] = []
            self.temp_dict["last_updated"] = 0.
            self.temp_dict["minmax_time_updated"] = 0.
            self.temp_dict["average_temperature"] = params.average_temperature
            self.temp_dict["min_temperature"] = params.min_temperature
            self.temp_dict["min_temperature_time"] = params.min_temperature_time
            self.temp_dict["min_temperature_local_hour"] = get_local_hour(self.params, params.min_temperature_time)
            self.temp_dict["max_temperature"] = params.max_temperature
            self.temp_dict["max_temperature_time"] = params.max_temperature_time
            self.temp_dict["max_temperature_local_hour"] = get_local_hour(self.params, params.max_temperature_time)
            self.temp_dict["current_temperature_external"] = (self.temp_dict["min_temperature"] + self.temp_dict[
                "max_temperature"]) / 2.
            self.temp_dict["current_humidity_external"] = params.average_humidity_external
            with open(self.temperature_file_name, 'w') as temperature_file:
                json.dump(self.temp_dict, temperature_file)
        time.sleep(self.params.lookup_sleep_time)
        self.dew_point = pmatic.utils.dew_point(self.temp_dict["current_temperature_external"],
                                                self.temp_dict["current_humidity_external"])

        # Invalidate statistics.
        self.max_forecast_temperature = None
        self.max_forecast_temperature_local_hour = None
        self.min_forecast_temperature = None
        self.min_forecast_temperature_local_hour = None
        self.average_forecast_temperature = None
        self.ventilation_max_forecast_temperature_local_hour = None
        self.ventilation_min_forecast_temperature_local_hour = None

    def update(self):
        # Do a new temperature measurement and update the temperature statistics
        self.current_time = time.time()
        local_hour = get_local_hour(self.params, self.current_time)
        if self.current_time - self.temp_dict["last_updated"] > self.params.temperature_update_interval:
            # If an internet connection is available, update temperature forecast values
            self.update_forecast()
            try:
                self.temp_dict["current_temperature_external"] = self.temperature_device_external.temperature.value
                self.temp_dict["current_humidity_external"] = self.temperature_device_external.humidity.value / 100.
                self.dew_point = pmatic.utils.dew_point(self.temp_dict["current_temperature_external"],
                                                        self.temp_dict["current_humidity_external"])
                if self.params.output_level > 2:
                    print_output("External temperature: " + str(self.temp_dict["current_temperature_external"]) +
                                 ", humidity: " + str(self.temp_dict["current_humidity_external"]) +
                                 ", dew point: " + str(self.dew_point))
                temp_object = [self.current_time, self.temp_dict["current_temperature_external"]]
                self.temp_dict["temperatures"].append(temp_object)
                self.temp_dict["last_updated"] = self.current_time

                # Update minima / maxima data at the first invocation after 18:00 local time,
                # but only if data have been recorded for at least 23 hours
                if self.current_time - self.temp_dict["minmax_time_updated"] > 82800. and 18. < local_hour < 24.:
                    if self.params.output_level > 1:
                        print_output("Updating average, maximum and minimum external temperatures:")
                    average_temperature = 0.
                    min_temperature = 100.
                    max_temperature = -100.
                    for temp_object_stored in self.temp_dict["temperatures"]:
                        if self.current_time - temp_object_stored[0] > 86400.:
                            self.temp_dict["temperatures"].remove(temp_object_stored)
                            continue
                        average_temperature += temp_object_stored[1]
                        local_hour = get_local_hour(self.params, temp_object_stored[0])
                        # Look for maximum temperature only between 1:00 and 6:00 p.m. local time
                        if 13. < local_hour < 18. and temp_object_stored[1] > max_temperature:
                            max_temperature = temp_object_stored[1]
                            max_temperature_time = temp_object_stored[0]
                            max_local_hour = local_hour
                        # Look for minimum temperature only between 3:00 and 9:00 a.m. local time
                        if 3. < local_hour < 9. and temp_object_stored[1] < min_temperature:
                            min_temperature = temp_object_stored[1]
                            min_temperature_time = temp_object_stored[0]
                            min_local_hour = local_hour
                    if max_temperature == -100. and min_temperature == 100. and self.params.output_level > 1:
                        print "No new maximum or minimum temperature found"
                    else:
                        self.temp_dict["average_temperature"] = average_temperature / len(
                            self.temp_dict["temperatures"])
                        if max_temperature > -100.:
                            if self.params.output_level > 1:
                                print "New maximum temperature: " + str(max_temperature) + ", Time of maximum: " + str(
                                    datetime.datetime.fromtimestamp(max_temperature_time))
                            self.temp_dict["max_temperature"] = max_temperature
                            self.temp_dict["max_temperature_time"] = max_temperature_time
                            self.temp_dict["max_temperature_local_hour"] = max_local_hour
                        if min_temperature < 100.:
                            if self.params.output_level > 1:
                                print "New minimum temperature: " + str(min_temperature) + ", Time of minimum: " + str(
                                    datetime.datetime.fromtimestamp(min_temperature_time))
                            self.temp_dict["min_temperature"] = min_temperature
                            self.temp_dict["min_temperature_time"] = min_temperature_time
                            self.temp_dict["min_temperature_local_hour"] = min_local_hour
                    # Find max / min temperature values and corresponding times in forecast records.
                    self.analyze_forecast()
                    if self.max_forecast_temperature is not None and self.params.output_level > 1:
                        print "New forecast maximum temperature: " + str(self.max_forecast_temperature) + \
                              ", Local hour of maximum: " + str(self.max_forecast_temperature_local_hour)
                    if self.min_forecast_temperature is not None and self.params.output_level > 1:
                        print "New forecast minimum temperature: " + str(self.min_forecast_temperature) + \
                              ", Local hour of minimum: " + str(self.min_forecast_temperature_local_hour)
                    self.temp_dict["minmax_time_updated"] = self.current_time
                    if self.ventilation_max_forecast_temperature_local_hour is not None and self.params.output_level > 1:
                        print "Local hour of maximum temperature next 24 hours: " + \
                              str(self.ventilation_max_forecast_temperature_local_hour)
                    if self.ventilation_min_forecast_temperature_local_hour is not None and self.params.output_level > 1:
                        print "Local hour of minimum temperature next 24 hours: " + \
                              str(self.ventilation_min_forecast_temperature_local_hour)
                with open(self.temperature_file_name, 'w') as temperature_file:
                    json.dump(self.temp_dict, temperature_file)
            except Exception as e:
                if self.params.output_level > 0:
                    print_output(repr(e))
            time.sleep(self.params.lookup_sleep_time)

    def update_forecast(self):
        """
        Connect with the OpenWeatherMap server and retrieve a five days temperature forecast

        :return: -
        """
        try:
            req = urllib2.Request(self.params.ow_url_fcst)
            response = urllib2.urlopen(req)
            output_fcst = response.read()
            json_out_fcst = json.loads(output_fcst)
            temperature_forecast = []
            count = json_out_fcst['cnt']
            # Build a list with the forecast temperature values along with the corresponding Unix timestamps
            for i in range(1, count):
                timestamp = json_out_fcst['list'][i]['dt']
                # date = json_out_fcst['list'][i]['dt_txt']
                temp = json_out_fcst['list'][i]['main']['temp']
                # print timestamp, date, temp
                temperature_forecast.append([timestamp, temp])
            # Replace the old list with forecast values with the new one
            self.temp_dict["temperatures_forecast"] = temperature_forecast
        except:
            # If not successful (e.g. no internet connection), leave the forecast values unchanged.
            return
        if self.params.output_level > 2:
            print_output("New temperature forecast downloaded from OpenWeatherMap")

    def analyze_forecast(self):
        """
        Look for maximum and minimum forecast temperatures and corresponding local hours, and compute the average
        temperature. The statistics are always based on whole day periods, with the maximum number of forecast days
        given by the max_temp_lookahead_time parameter.

        Additionally, times of maximum and minimum temperature are computed for the next day for ventilation control.

        All values are stored as instance variables.

        :return: -
        """
        # Compute the number of days for forecast statistics.
        self.forecast_days = min(self.compute_available_forecast_days(), self.params.max_temp_lookahead_time)
        if self.forecast_days > 0:
            (self.max_forecast_temperature, self.max_forecast_temperature_local_hour, \
             self.min_forecast_temperature, self.min_forecast_temperature_local_hour, \
             self.average_forecast_temperature) = self.compute_min_max_average(self.forecast_days)
        else:
            # Invalidate statistics if not enough forecast times are available.
            self.max_forecast_temperature = None
            self.max_forecast_temperature_local_hour = None
            self.min_forecast_temperature = None
            self.min_forecast_temperature_local_hour = None
            self.average_forecast_temperature = None
        # For ventilation control compute forecast times of temp max and min during the next day.
        if self.compute_available_forecast_days() > 0:
            (temp1, self.ventilation_max_forecast_temperature_local_hour, temp2,
             self.ventilation_min_forecast_temperature_local_hour, temp3) = self.compute_min_max_average(1)
        else:
            self.ventilation_max_forecast_temperature_local_hour = None
            self.ventilation_min_forecast_temperature_local_hour = None

    def compute_available_forecast_days(self):
        """
        Compute the number of whole days in the future for which temperature forecasts are available.

        :return: number of whole forecast days
        """
        if len(self.temp_dict["temperatures_forecast"]) == 0:
            return 0
        else:
            return floor((self.temp_dict["temperatures_forecast"][-1][0] - self.current_time) / 86400.)

    def compute_min_max_average(self, days_ahead):
        """
        Look for maximum and minimum forecast temperatures and corresponding local hours, and compute the average
        temperature. The statistics are always based on whole day periods, with the maximum number of forecast days
        given by the max_temp_lookahead_time parameter. All values are stored as instance variables and accessed by
        lookup funktions.

        :return: A tuple consisting of:
                - maximum forecast temperature
                - local hour of maximum
                - minimum forecast temperature
                - local hour of minimum
                - average forecast temperature
                If no temperature forecasts are stored, None is returned.
        """

        max_forecast_temp = -100.
        min_forecast_temp = 100.
        average_forecast_temp = 0.
        n_timestamps = 0
        for [timestamp, temperature] in self.temp_dict["temperatures_forecast"]:
            if (timestamp - self.current_time) / 86400. > days_ahead:
                break
            if timestamp >= self.current_time:
                n_timestamps += 1
                # Update average, minimum and maximum values.
                average_forecast_temp += temperature
                if temperature > max_forecast_temp:
                    max_forecast_temp = temperature
                    max_forecast_temp_timestamp = timestamp
                if temperature < min_forecast_temp:
                    min_forecast_temp = temperature
                    min_forecast_temp_timestamp = timestamp
        if n_timestamps > 0:
            # Translate Unix timestamps into local hours and compute average temperature.
            max_forecast_temp_local_hour = get_local_hour(self.params, max_forecast_temp_timestamp)
            min_forecast_temp_local_hour = get_local_hour(self.params, min_forecast_temp_timestamp)
            average_forecast_temp = average_forecast_temp / float(n_timestamps)
            return max_forecast_temp, max_forecast_temp_local_hour, min_forecast_temp, min_forecast_temp_local_hour, \
                   average_forecast_temp
        else:
            return None

    def temperature_condition(self):
        """
        Characterize the current temperature situation for setting the shutters. Different schemes can be selected with
        setting the parameter "shutter_control_scheme".

        :return: character string which characterizes the current temperature situation
        """

        if self.params.shutter_control_scheme == "average_temperature":
            # Control scheme based on average external temperatures (forecast or recorded):

            if self.average_forecast_temperature is not None:
                average_temperature = self.average_forecast_temperature
            else:
                average_temperature = self.temp_dict["average_temperature"]

            if average_temperature >= self.params.average_temperature_very_hot:
                if self.temp_dict["average_temperature"] < self.params.average_temperature_very_hot:
                    return "very-hot-fcst"
                else:
                    return "very-hot"
            elif average_temperature >= self.params.average_temperature_hot:
                if self.temp_dict["average_temperature"] < self.params.average_temperature_hot:
                    return "hot-fcst"
                else:
                    return "hot"
            elif average_temperature > self.params.average_temperature_cold:
                return "normal"
            else:
                return "cold"

        else:
            # Control scheme based on current and maximum temperatures:
            #
            # Compare the current and maximum temperatures with predefined threshold values. For the characterization
            # "very-hot" and "hot" both the current temperature and the maximum forecast temperature (or, if not
            # available,the maximum temperature of the previous day) are used. The temperature is called "cold" if the
            # maximum temperature of the previous day was below a certain threshold.

            if self.temp_dict["current_temperature_external"] > self.params.current_temperature_very_hot:
                return "very-hot"
            elif self.params.current_temperature_hot < self.temp_dict["current_temperature_external"] <= \
                    self.params.current_temperature_very_hot:
                if self.max_forecast_temperature is None and self.temp_dict[
                    "max_temperature"] > self.params.max_temperature_very_hot:
                    return "very-hot"
                elif self.max_forecast_temperature is not None and \
                                self.max_forecast_temperature > self.params.max_temperature_very_hot:
                    return "very-hot"
                else:
                    return "hot"
            elif self.max_forecast_temperature is None:
                if max(self.temp_dict["current_temperature_external"],
                       self.temp_dict["max_temperature"]) > self.params.max_temperature_hot:
                    return "hot"
                elif max(self.temp_dict["current_temperature_external"],
                         self.temp_dict["max_temperature"]) < self.params.max_temperature_cold:
                    return "cold"
                else:
                    return "normal"
            else:
                if self.max_forecast_temperature > self.params.max_temperature_very_hot:
                    return "very-hot-fcst"
                elif self.max_forecast_temperature > self.params.max_temperature_hot:
                    return "hot-fcst"
                elif self.max_forecast_temperature < self.params.max_temperature_cold:
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
    # Update temperature measurements and server forecast info at every call.
    params.temperature_update_interval = 0.

    while True:
        temperatures.update()
        temperatures.analyze_forecast()
        print_output("max. forecast temp.: " + str(temperatures.max_forecast_temperature) + ", at local hour: " +
                     str(temperatures.max_forecast_temperature_local_hour) + ", min. forecast temp.: " +
                     str(temperatures.min_forecast_temperature) + ", at local hour: " +
                     str(temperatures.min_forecast_temperature_local_hour) + ", average temp.: " +
                     str(temperatures.average_forecast_temperature) + ", No. forecast days: " +
                     str(temperatures.forecast_days) + ", next day max. at local hour: " +
                     str(temperatures.ventilation_max_forecast_temperature_local_hour) +
                     ", next day min. at local hour: " +
                     str(temperatures.ventilation_min_forecast_temperature_local_hour))
        if params.output_level > 2:
            print "temperature condition: ", temperatures.temperature_condition()
        time.sleep(params.main_loop_sleep_time)
