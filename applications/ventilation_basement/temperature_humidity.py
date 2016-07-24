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

from miscellaneous import *


class temperature_humidity(object):
    """This class manages the readouts from internal and external temperature/humidity meters.

    The temperature_humidity object keeps a list of external temperature readings, each stored together with the
    corresponding Unix timestamp. Readings which are more than one day old are dropped from the list. This list is the
    basis for computing the maximum and minimum temperatures.

    """

    def __init__(self, params, temperature_device_external, temperature_device_internal):
        self.params = params
        self.temperature_device_external = temperature_device_external
        self.temperature_device_internal = temperature_device_internal

        self.temperatures = []
        self.minmax_time_updated = time.time()
        self.min_temperature = self.params.min_temperature
        self.min_temperature_time = self.params.min_temperature_time
        self.max_temperature = self.params.max_temperature
        self.max_temperature_time = self.params.max_temperature_time
        self.average_humidity_external = self.params.average_humidity_external

        self.update_temperature_humidity()

    def update_temperature_humidity(self):
        """
        Read the current values for external / internal temperature and humidity and update minimum and maximum
        temperatures, together with the UTC timestamps for which those values were attained, as well as the average
        external humidity.

        :return: -
        """

        self.current_temperature_external = self.temperature_device_external.temperature.value
        # Convert humidity from percent to a float between 0. and 1.
        self.current_humidity_external = self.temperature_device_external.humidity.value / 100.

        self.current_temperature_internal = self.temperature_device_internal.temperature.value
        # Convert humidity from percent to a float between 0. and 1.
        self.current_humidity_internal = self.temperature_device_internal.humidity.value / 100.

        if self.params.output_level > 2:
            print_output("T int: " + str(self.current_temperature_internal) + ", H int: " + str(
                self.current_humidity_internal) + ", T ext: " + str(
                self.current_temperature_external) + ", H ext: " + str(
                self.current_humidity_external))
        # Unix timestamp (counted in seconds since 1970.0)
        current_time = time.time()
        temp_object = [current_time, self.current_temperature_external, self.current_humidity_external]
        lh = get_local_hour(self.params, current_time)

        # Update minima / maxima data at the first invocation after 12:00 a.m. local time,
        # but only if data have been recorded at least since 01:00 p.m. on previous day
        if current_time - self.minmax_time_updated > 82800. and 12. < lh < 12.1:
            self.min_temperature = 100.
            self.max_temperature = -100.
            self.average_humidity_external = -1.
            for to in self.temperatures:
                lh = get_local_hour(self.params, to[0])
                # Look for maximum temperature only between 1:00 and 6:00 p.m. local time
                if to[1] > self.max_temperature and 13. < lh < 18.:
                    self.max_temperature = to[1]
                    self.max_temperature_time = to[0]
                # Look for minimum temperature only between 3:00 and 9:00 a.m. local time
                if to[1] < self.min_temperature and 3. < lh < 9.:
                    self.min_temperature = to[1]
                    self.min_temperature_time = to[0]
                # Compute the average external humidity with all recorded values
                self.average_humidity_external += to[2]
            self.average_humidity_external /= float(len(self.temperatures))
            if self.params.output_level > 1:
                print ""
                print_output(" Updating maximum and minimum external temperatures:\nNew maximum temperature: " + str(
                    self.max_temperature) + ", Time of maximum: " + str(datetime.datetime.fromtimestamp(
                    self.max_temperature_time)) + " \nNew minimum temperature: " + str(
                    self.min_temperature) + ", Time of minimum: " + str(datetime.datetime.fromtimestamp(
                    self.min_temperature_time)) + "\nNew average external humidity: " + str(
                    self.average_humidity_external * 100.) + "%")

            self.minmax_time_updated = current_time
            self.temperatures = [temp_object]
        else:
            self.temperatures.append(temp_object)
