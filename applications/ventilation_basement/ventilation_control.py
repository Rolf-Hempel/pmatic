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
from os.path import expanduser, isfile

import pmatic


class temperature_humidity(object):
    """This class manages the readouts from internal and external temperature/humidity meters.

    The temperature_humidity object keeps a list of external temperature readings, each stored together with the
    corresponding Unix timestamp. Readings which are more than one day old are dropped from the list. This list is the
    basis for computing the maximum and minimum temperatures.

    """

    def __init__(self, temperature_device_external, temperature_device_internal):
        self.temperature_device_external = temperature_device_external
        self.temperature_device_internal = temperature_device_internal

        self.temperatures = []
        self.minmax_time_updated = 0.
        self.min_temperature_time = 0.
        self.max_temperature_time = 0.

        # Time in seconds between two consecutive computations of minimum and maximum temperatures
        self.min_time_between_minmax_updates = 86400.
        # Time period in seconds for which temperature measurements are kept for min/max computations
        self.retention_time_for_temperature_measurements = 86400.

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

        # Unix timestamp (counted in seconds since 1970.0)
        current_time = time.time()
        temp_object = [current_time, current_temperature_external]
        self.temperatures.append(temp_object)

        # Update minimum and maximum temperature only once per "self.min_time_between_minmax_updates" seconds
        if current_time - self.minmax_time_updated >= self.min_time_between_minmax_updates:
            if len(self.temperatures) > 0:
                # Drop entries older than retention time:
                for i in range(len(self.temperatures)):
                    if current_time - self.temperatures[i][0] < self.retention_time_for_temperature_measurements:
                        break
                self.temperatures = self.temperatures[i:]

            self.minmax_time_updated = current_time
            self.min_temperature = 100.
            self.max_temperature = -100.
            for to in self.temperatures:
                if to[1] > self.max_temperature:
                    self.max_temperature = to[1]
                    self.max_temperature_time_new = to[0]
                if to[1] < self.min_temperature:
                    self.min_temperature = to[1]
                    self.min_temperature_time_new = to[0]
            if self.max_temperature_time_new != self.max_temperature_time:
                print "\n", date_and_time(), \
                    " Updating maximum external temperature: New maximum temperature: ", self.max_temperature, \
                    ", Time of maximum: ", datetime.datetime.fromtimestamp(self.max_temperature_time_new)
                self.max_temperature_time = self.max_temperature_time_new
            if self.min_temperature_time_new != self.min_temperature_time:
                print "\n", date_and_time(), \
                    " Updating minimum external temperature: New minimum temperature: ", self.min_temperature, \
                    ", Time of minimum: ", datetime.datetime.fromtimestamp(self.min_temperature_time_new)
                self.min_temperature_time = self.min_temperature_time_new
        return (current_temperature_internal, current_humidity_internal, current_temperature_external,
                current_humidity_external, self.max_temperature, self.min_temperature_time, self.max_temperature_time)


class switch(object):
    """This class controls the switch(es) of the ventilation devic(es). Basically, a ventilator is switched on only if
    the outside dew point temperature is below the inside air temperature. Additionally, the ventilator is switched on
    for periods of 1000 seconds each, with pauses in between. The distribution of the active periods over the day is
    defined by a switch pattern. Two different patterns are set: The first one is applied if the maximum outside
    temperature is below a certain threshold. In order to get as warm air as possible into the room, more active periods
    occur during the day than at night. If the outside temperature is high, ventilation takes place preferably during
    the night.

    """

    def __init__(self, switch_device):
        self.switch_device = switch_device
        # self.temp_pattern = [[100, 110], [200, 210], [300, 310], [400, 410], [500, 510], [600, 610],
        #                          [3000., 4000.], [8000., 9000.], [13000., 14000.], [18000., 19000.], \
        self.temp_pattern = [[3000., 4000.], [8000., 9000.], [13000., 14000.], [18000., 19000.], \
                                  [26000., 27000.], [36000., 37000.], [46000., 47000.], [56000., 57000.], \
                                  [61000., 62000.], [69000., 70000.], [77000., 78000.], [83000., 84000.]]
        # Definition of the threshold temperature
        self.transition_temperature = 5.

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
                switch_on_time = True
                break

        dew_point_external = pmatic.utils.dew_point(current_temperature_external, current_humidity_external)

        try:
            if self.switch_device.is_on and not switch_on_time:
                print date_and_time(), " Switching ", self.switch_device.name, " off"
                self.switch_device.switch_off()
            elif switch_on_time and not self.switch_device.is_on and dew_point_external < current_temperature_internal:
                print date_and_time(), " Switching ", self.switch_device.name, " on, T int: ", \
                    current_temperature_internal, ", T ext: ", current_temperature_external, \
                    ", Dew point: ", dew_point_external
                self.switch_device.switch_on()
        except Exception as e:
            print e


def date_and_time():
    """Compute the current date and time.

    :return: Character string with current date and time information
    """
    return datetime.datetime.fromtimestamp(time.time())


def look_up_device(dev_name):
    """Look up the device by its name

    Args:
        dev_name: device name (utf-8 string)

    Returns: the device object

    """
    try:
        devices = ccu.devices.query(device_name=dev_name)._devices.values()
    except Exception as e:
        print e
    if len(devices) == 1:
        print dev_name
        return devices[0]
    elif len(devices) > 1:
        print date_and_time(), " More than one device with name ", dev_name, " found, first one taken"
    else:
        print date_and_time(), " Error: No device with name ", dev_name, " found, execution halted."
        sys.exit(1)


if __name__ == "__main__":

    # Look for config file. If found: read credentials for remote CCU access
    config_file_name = expanduser("~") + "/.pmatic.config"
    if isfile(config_file_name):
        print "Remote execution on PC:"
        file = open(config_file_name, 'r')
        addr, user, passwd = file.read().splitlines()
        print "CCU address: ", addr, ", user: ", user, ", password: ", passwd
        ccu = pmatic.CCU(address=addr, credentials=(user, passwd), connect_timeout=5)
    else:
        print "Local execution on CCU:"
        ccu = pmatic.CCU()
        # For execution on CCU redirect stdout to a protocol file
        sys.stdout = codecs.open('/media/sd-mmcblk0/protocols/ventilation.txt', encoding='utf-8', mode='a')

    # Look up devices for outside and internal temperature/humidity measurement and ventilator switching
    print "\n", date_and_time(), " Starting ventilation control program\nDevices used:"
    temperature_device_external = look_up_device(u'Temperatur- und Feuchtesensor außen')
    temperature_device_internal = look_up_device(u'Temperatur- und Feuchtesensor Gartenkeller')
    switch_device = look_up_device(u"Steckdosenschalter Gartenkeller")

    th = temperature_humidity(temperature_device_external, temperature_device_internal)
    sw = switch(switch_device)

    while True:
        current_temperature_internal, current_humidity_internal, current_temperature_external, \
        current_humidity_external, max_temperature, min_temperature_time, max_temperature_time = \
            th.update_temperature_humidity()
        sw.ventilator_state_update(current_temperature_internal, current_temperature_external,
                                   current_humidity_external, max_temperature, min_temperature_time,
                                   max_temperature_time)
        time.sleep(120.)
