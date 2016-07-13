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

import datetime
import sys
import time
import codecs

import pmatic


class temperature_humidity(object):
    """This class manages the readouts from internal and external temperature/humidity meters. For both internal and
    external measurements, the readouts from several devices can be averaged.

    The temperature_humidity object keeps a list of external temperature readings, each stored together with the
    corresponding Unix timestamp. Readings which are more than one day old are dropped from the list. This list is the
    basis for computing the maximum and minimum temperatures.

    """

    def __init__(self, temperature_devices_external, temperature_devices_internal):
        self.temperature_devices_external = temperature_devices_external
        self.temperature_devices_internal = temperature_devices_internal

        self.temperatures = []
        self.minmax_time_updated = 0.
        self.update_temperature_humidity()

    def update_temperature_humidity(self):
        """
        Read the current values for external / internal temperature and humidity and update minimum and maximum
        temperatures.
        :return: current values for internal and external temperature and humidity, maximum external temperature
        and the Unix timestamp of the minimum external temperature, both computed for the last 24 hours.
        """
        current_temperature_external = 0.
        current_humidity_external = 0.
        for device in self.temperature_devices_external:
            current_temperature_external += device.temperature.value
            current_humidity_external += device.humidity.value
        current_temperature_external = current_temperature_external / len(self.temperature_devices_external)
        # Convert humidity from percent to a float between 0. and 1.
        current_humidity_external = current_humidity_external / (100.*len(self.temperature_devices_external))
        current_temperature_internal = 0.
        current_humidity_internal = 0.
        for device in self.temperature_devices_internal:
            current_temperature_internal += device.temperature.value
            current_humidity_internal += device.humidity.value
        current_temperature_internal = current_temperature_internal / len(self.temperature_devices_internal)
        current_humidity_internal = current_humidity_internal / len(self.temperature_devices_internal)
        # Unix timestamp (counted in seconds since 1970.0)
        current_time = time.time()
        temp_object = [current_time, current_temperature_external]
        self.temperatures.append(temp_object)

        # Update minimum and maximum temperature only once per day
        if current_time - self.minmax_time_updated >= 86400.:
            if len(self.temperatures) > 0:
                # Drop entries older than one day
                for i in range(len(self.temperatures)):
                    if current_time - self.temperatures[i][0] < 86400.:
                        break
                self.temperatures = self.temperatures[i:]

            self.minmax_time_updated = current_time
            self.index_max = -1
            self.index_min = -1
            self.min_temperature = 100.
            self.max_temperature = -100.
            for to in self.temperatures:
                if to[1] > self.max_temperature:
                    self.max_temperature = to[1]
                    self.max_temperature_time = to[0]
                if to[1] < self.min_temperature:
                    self.min_temperature = to[1]
                    self.min_temperature_time = to[0]
            print "\n", date_and_time(), \
                " Updating minimum and maximum external temperatures:\nCurrent temperature: ", \
                current_temperature_external, ", New minimum temperature: ", \
                self.min_temperature, ", new maximum temperature: ", self.max_temperature, "\n"
        return (current_temperature_internal, current_humidity_internal, current_temperature_external,
                current_humidity_external, self.max_temperature, self.min_temperature_time)


class switch(object):
    """This class controls the switch(es) of the ventilation devic(es). Basically, a ventilator is switched on only if
    the outside dew point temperature is below the inside air temperature. Additionally, the ventilator is switched on
    for periods of 1000 seconds each, with pauses in between. The distribution of the active periods over the day is
    defined by a switch pattern. Two different patterns are set: The first one is applied if the maximum outside
    temperature is below a certain threshold. In order to get as warm air as possible into the room, more active periods
    occur during the day than at night. If the outside temperature is high, ventilation takes place preferably during
    the night.

    """

    def __init__(self, switch_devices):
        self.switch_devices = switch_devices
        self.low_temp_pattern = [[10000., 11000.], [20000., 21000.], [29000., 30000.], [35000., 36000.], \
                                 [40000., 41000.], [45000., 46000.], [50000., 51000.], [55000., 56000.], \
                                 [61000., 62000.], [70000., 71000.], [80000., 81000.]]
        self.high_temp_pattern = [[3000., 4000.], [8000., 9000.], [13000., 14000.], [18000., 19000.], \
                                  [26000., 27000.], [36000., 37000.], [46000., 47000.], [56000., 57000.], \
                                  [61000., 62000.], [69000., 70000.], [77000., 78000.], [83000., 84000.]]
        # Definition of the threshold temperature
        self.transition_temperature = 10.

    def ventilator_state_update(self, current_temperature_internal, current_temperature_external,
                                current_humidity_external, max_temperature, min_temperature_time):
        """
        Switch the ventilator(s) on/off depending on current temperature and humidity measurements and information about
        the maximum temperature and the time when the minimum temperature was attained.

        :param current_temperature_internal: Current internal air temperature (Celsius)
        :param current_temperature_external: Current outside air temperature (Celsius)
        :param current_humidity_external: Current outside relative humidity (0. for 0%, 1. for 100%)
        :param max_temperature: Maximal outside air temperature during the last 24 hours (Celsius)
        :param min_temperature_time: Unix timestamp of minimal outside air temperature during the last 24 hours
        :return: -
        """
        if max_temperature > self.transition_temperature:
            temp_pattern = self.high_temp_pattern
        else:
            temp_pattern = self.low_temp_pattern
        switch_on_time = False
        for interval in temp_pattern:
            if interval[0] < time.time() - min_temperature_time < interval[1]:
                switch_on_time = True
                break

        dew_point_external = pmatic.utils.dew_point(current_temperature_external, current_humidity_external)

        for switch_device in self.switch_devices:
            if switch_device.is_on and not switch_on_time:
                print date_and_time(), " Switching ", switch_device.name, " off"
                switch_device.switch_off()
            elif switch_on_time and switch_device.is_off and dew_point_external < current_temperature_internal:
                print date_and_time(), " Switching ", switch_device.name, " on, T int: ", \
                    current_temperature_internal, ", T ext: ", current_temperature_external, \
                    ", Dew point: ", dew_point_external
                switch_device.switch_on()


def date_and_time():
    """Compute the current date and time.

    :return: Character string with current date and time information
    """
    return datetime.datetime.fromtimestamp(time.time())


if __name__ == "__main__":
    # ccu = pmatic.CCU()
    # sys.stdout = codecs.open('/media/sd-mmcblk0/protocols/ventilation.txt', encoding='utf-8', mode='a')
    ccu = pmatic.CCU(address="http://192.168.0.51", credentials=("rolf", "Px9820rH"), connect_timeout=5)

    # Look up outside and internal temperature/humidity measuring devices
    print "\n", date_and_time(), " Starting ventilation control program\nDevices used:"
    temperature_devices_external = ccu.devices.query(device_type=[u'HM-WDS10-TH-O'])
    for device in temperature_devices_external:
        print "External temperature device: ", device.name
    if len(temperature_devices_external) == 0:
        print "Error: No external thermometer found."
        sys.exit(1)
    temperature_devices_internal = ccu.devices.query(device_name=u'Temperatur- und Feuchtesensor Gartenkeller')
    for device in temperature_devices_internal:
        print "Internal temperature device: ", device.name
    if len(temperature_devices_internal) == 0:
        print "Error: No external thermometer found."
        sys.exit(1)
    # Look up name of switch devices
    switch_devices = ccu.devices.query(device_name=u"Steckdosenschalter Gartenkeller")
    for device in switch_devices:
        print "Switch device: ", device.name
    if len(switch_devices) == 0:
        print "Error: No switch device found."
        sys.exit(1)

    th = temperature_humidity(temperature_devices_external, temperature_devices_internal)
    sw = switch(switch_devices)

    while True:
        current_temperature_internal, current_humidity_internal, current_temperature_external, \
        current_humidity_external, max_temperature, min_temperature_time = \
            th.update_temperature_humidity()
        sw.ventilator_state_update(current_temperature_internal, current_temperature_external,
                                   current_humidity_external, max_temperature, min_temperature_time)
        time.sleep(120)
