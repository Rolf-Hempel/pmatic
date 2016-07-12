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

import sys
import time

import pmatic


class temperature_humidity(object):
    def __init__(self, temperature_devices_external, temperature_devices_internal):
        self.temperature_devices_external = temperature_devices_external
        self.temperature_devices_internal = temperature_devices_internal

        self.temperatures = []
        self.minmax_time_updated = 0.
        self.update_temperature_humidity()

    def update_temperature_humidity(self):
        current_temperature_external = 0.
        current_humidity_external = 0.
        for device in self.temperature_devices_external:
            current_temperature_external += device.temperature.value
            current_humidity_external += device.humidity.value
        current_temperature_external = current_temperature_external / len(self.temperature_devices_external)
        current_humidity_external = current_humidity_external / len(self.temperature_devices_external)
        current_temperature_internal = 0.
        current_humidity_internal = 0.
        for device in self.temperature_devices_internal:
            current_temperature_internal += device.temperature.value
            current_humidity_internal += device.humidity.value
        current_temperature_internal = current_temperature_internal / len(self.temperature_devices_internal)
        current_humidity_internal = current_humidity_internal / len(self.temperature_devices_internal)
        current_time = time.time()
        temp_object = [current_time, current_temperature_external]
        self.temperatures.append(temp_object)

        for i in range(len(self.temperatures)):
            if current_time - self.temperatures[i][0] < 86400.:
                break
        self.temperatures = self.temperatures[i:]

        if current_time - self.minmax_time_updated >= 86400.:
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
        return (current_temperature_internal, current_humidity_internal, current_temperature_external,
                current_humidity_external, self.max_temperature, self.min_temperature_time)


class switch(object):
    def __init__(self, switch_devices):
        self.switch_devices = switch_devices
        self.low_temp_pattern = [[10000., 11000.], [20000., 21000.], [29000., 30000.], [35000., 36000.], \
                                 [40000., 41000.], [45000., 46000.], [50000., 51000.], [55000., 56000.], \
                                 [61000., 62000.], [70000., 71000.], [80000., 81000.]]
        self.high_temp_pattern = [[3000., 4000.], [8000., 9000.], [13000., 14000.], [18000., 19000.], \
                                  [26000., 27000.], [36000., 37000.], [46000., 47000.], [56000., 57000.], \
                                  [61000., 62000.], [69000., 70000.], [77000., 78000.], [83000., 84000.]]
        self.transition_temperature = 10.

    def ventilator_state_update(self, current_temperature_internal, current_temperature_external,
                                current_humidity_external, max_temperature, min_temperature_time):
        if max_temperature > self.transition_temperature:
            temp_pattern = self.high_temp_pattern
        else:
            temp_pattern = self.low_temp_pattern
        switch_on_time = False
        for interval in temp_pattern:
            if interval[0] < time.time() - min_temperature_time < interval[1]:
                switch_on_time = True
                break
        for switch_device in self.switch_devices:
            if switch_device.is_on() and not switch_on_time:
                switch_device.switch_off()
            elif switch_device.is_off() and pmatic.utils.dew_point(current_temperature_external,
                                            current_humidity_external) < current_temperature_internal:
                switch_device.switch_on()


if __name__ == "__main__":
    # ccu = pmatic.CCU()
    # sys.stdout = open('/media/sd-mmcblk0/protocols/ventilation', 'a')
    ccu = pmatic.CCU(address="http://192.168.0.51", credentials=("rolf", "Px9820rH"), connect_timeout=5)
    temperature_devices_external = ccu.devices.query(device_type=[u'HM-WDS10-TH-O'])
    for device in temperature_devices_external:
        print "External temperature device: ", device.name
    if len(temperature_devices_external) == 0:
        print "Error: No external thermometer found."
        sys.exit(1)
    temperature_devices_internal = ccu.devices.query(device_type=[u'HM-WDS40-TH-I-2'])
    for device in temperature_devices_internal:
        print "Internal temperature device: ", device.name
    if len(temperature_devices_internal) == 0:
        print "Error: No external thermometer found."
        sys.exit(1)
    switch_devices = ccu.devices.query(device_name=u"Steckdosenschalter Gartenkeller")
    for device in switch_devices:
        print "Switch device: ", device.name
    if len(switch_devices) == 0:
        print "Error: No switch device found."
        sys.exit(1)

    temperature_external_object = temperature_humidity(temperature_devices_external, temperature_devices_internal)
    switch_object = switch(switch_devices)

    while True:
        current_temperature_internal, current_humidity_internal, current_temperature_external,\
        current_humidity_external, max_temperature, min_temperature_time = \
            temperature_external_object.update_temperature_humidity()
        switch_object.ventilator_state_update(current_temperature_internal, current_temperature_external,
                                              current_humidity_external, max_temperature, min_temperature_time)
        time.sleep(120)
