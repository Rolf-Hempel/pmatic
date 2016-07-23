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
from parameters import parameters


class temperature_humidity(object):
    """This class manages the readouts from internal and external temperature/humidity meters.

    The temperature_humidity object keeps a list of external temperature readings, each stored together with the
    corresponding Unix timestamp. Readings which are more than one day old are dropped from the list. This list is the
    basis for computing the maximum and minimum temperatures.

    """

    def __init__(self, params, longitude, temperature_device_external, temperature_device_internal):
        self.params = params
        self.utc_shift = longitude / 15.
        self.temperature_device_external = temperature_device_external
        self.temperature_device_internal = temperature_device_internal

        self.temperatures = []
        self.minmax_time_updated = time.time()
        self.min_temperature = 5.
        # Set default time stamp of temperature minimum to 4:00 a.m. UTC
        self.min_temperature_time = self.params.min_temperature_time
        self.max_temperature = 10.
        # Set default time stamp of temperature maximum to 12:00 a.m. UTC
        self.max_temperature_time = self.params.max_temperature_time

        self.update_temperature_humidity()

    def update_temperature_humidity(self):
        """
        Read the current values for external / internal temperature and humidity and update minimum and maximum
        temperatures.
        :return: current values for internal and external temperature and humidity, the maximum external temperature
        and the Unix timestamps of the minimum and maximum external temperature, computed for the period given
        by the parameter "self.retention_time_for_temperature_measurements" (in seconds).
        """

        current_temperature_external = self.temperature_device_external.temperature.value
        # Convert humidity from percent to a float between 0. and 1.
        current_humidity_external = self.temperature_device_external.humidity.value / 100.

        current_temperature_internal = self.temperature_device_internal.temperature.value
        # Convert humidity from percent to a float between 0. and 1.
        current_humidity_internal = self.temperature_device_internal.humidity.value / 100.

        if params.output_level > 2:
            print_output("T int: " + str(current_temperature_internal) + ", H int: " + str(
                current_humidity_internal) + ", T ext: " + str(current_temperature_external) + ", H ext: " + str(
                current_humidity_external))
        # Unix timestamp (counted in seconds since 1970.0)
        current_time = time.time()
        temp_object = [current_time, current_temperature_external]
        lh = self.get_local_hour(current_time)

        # Update minima / maxima data at the first invocation after 12:00 a.m. local time,
        # but only if data have been recorded at least since 01:00 p.m. on previous day
        if current_time - self.minmax_time_updated > 82800. and 12. < lh < 12.1:
            self.min_temperature = 100.
            self.max_temperature = -100.
            for to in self.temperatures:
                lh = self.get_local_hour(to[0])
                # Look for maximum temperature only between 1:00 and 6:00 p.m. local time
                if to[1] > self.max_temperature and 13. < lh < 18.:
                    self.max_temperature = to[1]
                    self.max_temperature_time = to[0]
                # Look for minimum temperature only between 3:00 and 9:00 a.m. local time
                if to[1] < self.min_temperature and 3. < lh < 9.:
                    self.min_temperature = to[1]
                    self.min_temperature_time = to[0]
            if self.params.output_level > 1:
                print ""
                print_output(" Updating maximum and minimum external temperatures:\nNew maximum temperature: " + str(
                    self.max_temperature) + ", Time of maximum: " + str(datetime.datetime.fromtimestamp(
                    self.max_temperature_time)) + " \nNew minimum temperature: " + str(
                    self.min_temperature) + ", Time of minimum: " + str(datetime.datetime.fromtimestamp(
                    self.min_temperature_time)))

            self.minmax_time_updated = current_time
            self.temperatures = [temp_object]
        else:
            self.temperatures.append(temp_object)

        return (current_temperature_internal, current_humidity_internal, current_temperature_external,
                current_humidity_external, self.max_temperature, self.min_temperature_time, self.max_temperature_time)

    def get_local_hour(self, timestamp):
        """
        Compute the number of hours passed since local midnight.

        :param timestamp: Unix timestamp (seconds passed since Jan. 1st, 1970, 0:00 UTC)
        :return: the number of hours since local midnight. Examples: 0. for midnight, 12. for local noon, 12.5 for
                 half an hour after local noon.
        """
        return (timestamp / 3600. + self.utc_shift) % 24.


class switch(object):
    """This class controls the switch(es) of the ventilation devic(es). Basically, a ventilator is switched on only if
    the outside dew point temperature is below the inside air temperature. Additionally, the ventilator is switched on
    for periods of 1000 seconds each, with pauses in between. The distribution of the active periods over the day is
    defined by a switch pattern. Two different patterns are set: The first one is applied if the maximum outside
    temperature is below a certain threshold. In order to get as warm air as possible into the room, more active periods
    occur during the day than at night. If the outside temperature is high, ventilation takes place preferably during
    the night.

    """

    def __init__(self, params, switch_device):
        self.params = params
        self.switch_device = switch_device
        self.temp_pattern = [[3000., 4000.], [8000., 9000.], [13000., 14000.], [19000., 20000.], \
                             [26000., 27000.], [36000., 37000.], [46000., 47000.], [56000., 57000.], \
                             [65000., 66000.], [73000., 74000.], [79000., 80000.], [84000., 85000.]]
        # Definition of the threshold temperature
        self.transition_temperature = self.params.transition_temperature

    def ventilator_state_update(self, current_temperature_internal, current_temperature_external,
                                current_humidity_external, max_temperature, min_temperature_time, max_temperature_time):
        """
        Switch the ventilator(s) on/off depending on current temperature and humidity measurements and information about
        the maximum temperature and the time when the minimum temperature was attained.

        If the outside temperature is high, the switch pattern starts with the time of minimum temperature. Since
        the active intervals are concentrated towards the beginning and the end of the pattern, ventilation takes
        place mostly around minimum temperature. If the outside temperature is low, the pattern starts with the time
        of maximum temperature. This way most ventilation intervals occur around maximum outside temperature.

        :param current_temperature_internal: Current internal air temperature (Celsius)
        :param current_temperature_external: Current outside air temperature (Celsius)
        :param current_humidity_external: Current outside relative humidity (0. for 0%, 1. for 100%)
        :param max_temperature: Maximal outside air temperature during the last 24 hours (Celsius)
        :param min_temperature_time: Unix timestamp of the recent outside air temperature minimum (seconds)
        :param max_temperature_time: Unix timestamp of the recent outside air temperature maximum (seconds)
        :return: -
        """

        # Set the origin of the switch pattern according to the maximum outside temperature
        if max_temperature > self.transition_temperature:
            temp_pattern_origin = min_temperature_time
        else:
            temp_pattern_origin = max_temperature_time
        switch_on_time = False
        for interval in self.temp_pattern:
            if interval[0] < (time.time() - temp_pattern_origin) % 86400. < interval[1]:
                interval_index = self.temp_pattern.index(interval)
                switch_on_time = True
                break

        dew_point_external = pmatic.utils.dew_point(current_temperature_external, current_humidity_external)

        try:
            if self.switch_device.is_on and not switch_on_time:
                if self.params.output_level > 1:
                    print_output(" Switching " + self.switch_device.name + " off")
                self.switch_device.switch_off()
            elif switch_on_time and not self.switch_device.is_on and dew_point_external < current_temperature_internal:
                if self.params.output_level > 1:
                    print_output(" Switching " + self.switch_device.name + " on, Interval index: " + str(interval_index)
                                 + ", T int: " + str(current_temperature_internal) + ", T ext: "
                                 + str(current_temperature_external) + ", Dew point: " + str(dew_point_external))
                self.switch_device.switch_on()
        except Exception as e:
            print e


def date_and_time():
    """Compute the current date and time.

    :return: Character string with current date and time information
    """
    return datetime.datetime.fromtimestamp(time.time())


def look_up_device(params, dev_name):
    """Look up the device by its name. If two devices are found with the same name, print an error message and exit.

    Args:
        params: parameter object
        dev_name: device name (utf-8 string)

    Returns: the device object

    """
    try:
        devices = ccu.devices.query(device_name=dev_name)._devices.values()
    except Exception as e:
        print e
    if len(devices) == 1:
        if params.output_level > 0:
            print dev_name
        return devices[0]
    elif len(devices) > 1:
        print " More than one device with name ", dev_name, " found, first one taken."
    else:
        print " Error: No device with name ", dev_name, " found, execution halted."
        sys.exit(1)


def print_output(output_string):
    print datetime.datetime.fromtimestamp(time.time()), output_string


if __name__ == "__main__":

    params = parameters()

    if params.hostname == "homematic-ccu2":
        # For execution on CCU redirect stdout to a protocol file
        sys.stdout = codecs.open('/media/sd-mmcblk0/protocols/ventilation.txt', encoding='utf-8', mode='a')
        if params.output_level > 0:
            print ""
            print_output(
                "++++++++++++++++++++++++++++++++++ Start Local Execution on CCU +++++++++++++++++++++++++++++++++++++")
        ccu = pmatic.CCU()
    else:
        if params.output_level > 0:
            print ""
            print_output(
                "++++++++++++++++++++++++++++++++++ Start Remote Execution on PC +++++++++++++++++++++++++++++++++++++")
        ccu = pmatic.CCU(address=params.ccu_address, credentials=(params.user, params.password), connect_timeout=5)

    if params.output_level > 1:
        params.print_parameters()

    # Look up devices for outside and internal temperature/humidity measurement and ventilator switching
    if params.output_level > 0:
        print ""
        print_output("Devices used:")
    temperature_device_external = look_up_device(params, u'Temperatur- und Feuchtesensor außen')
    temperature_device_internal = look_up_device(params, u'Temperatur- und Feuchtesensor Gartenkeller')
    switch_device = look_up_device(params, u"Steckdosenschalter Gartenkeller")

    # Set geographical longitude (in degrees, positive to the East) of site
    longitude = params.longitude
    th = temperature_humidity(params, longitude, temperature_device_external, temperature_device_internal)
    sw = switch(params, switch_device)

    while True:
        if params.update_parameters():
            if params.output_level > 1:
                print "\nParameters have changed!"
                params.print_parameters()

        current_temperature_internal, current_humidity_internal, current_temperature_external, \
        current_humidity_external, max_temperature, min_temperature_time, max_temperature_time = \
            th.update_temperature_humidity()
        sw.ventilator_state_update(current_temperature_internal, current_temperature_external,
                                   current_humidity_external, max_temperature, min_temperature_time,
                                   max_temperature_time)
        time.sleep(params.main_loop_sleep_time)
