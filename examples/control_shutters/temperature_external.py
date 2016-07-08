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

import time

import pmatic


class temperature_external(object):
    def __init__(self, temperature_devices):
        self.temperature_devices = temperature_devices

        self.temperatures = []
        self.minmax_time_updated = 0.
        self.update_temperature()

    def update_temperature(self):
        current_temperature = 0.
        for device in self.temperature_devices:
            current_temperature += device.temperature
        current_temperature = current_temperature / self.number_devices
        current_time = time.time()
        temp_object = [current_time, current_temperature]
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
        return (self.max_temperature, self.min_temperature_time)


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
        self.ventilator_on = False

    def ventilator_state_update(self, max_temperature, min_temperature_time):
        if max_temperature > self.transition_temperature:
            temp_pattern = self.high_temp_pattern
        else:
            temp_pattern = self.low_temp_pattern
        switch_on = False
        for interval in temp_pattern:
            if interval[0] < time.time() - min_temperature_time < interval[1]:
                switch_on = True
                break
        for device in self.switch_devices:
            if device.is_on() != switch_on:
                device.toggle()


if __name__ == "__main__":
    ccu = pmatic.CCU(address="http://192.168.0.51", credentials=("Admin", "xxx"), connect_timeout=5)
    temperature_devices = ccu.devices.query(device_type=["xxx"])
    number_devices = len(temperature_devices)
    if number_devices == 0:
        print "Error: No external thermometer found."
    switch_devices = ccu.devices.query(device_name=u"HM-LC-Sw1-Pl-DN-R1 xxxx")
    number_devices = len(switch_devices)
    if number_devices == 0:
        print "Error: No switch device found."

    temperature_external_object = temperature_external(temperature_devices)
    switch_object = switch(switch_devices)

    while True:
        max_temperature, min_temperature_time = temperature_external_object.update_temperature()
        switch_object.ventilator_state_update(max_temperature, min_temperature_time)
        time.sleep(120)
