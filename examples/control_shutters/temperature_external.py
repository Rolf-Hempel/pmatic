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
    def __init__(self, ccu):
        self.devices = ccu.devices.query(device_type=["xxx"])
        self.number_devices = len(self.devices)
        if self.number_devices==0:
            print "Error: No external thermometer found."
        self.temperatures = []
        self.update_temperature()

    def update_temperature(self):
        current_temperature = 0.
        for device in self.devices:
            current_temperature += device.temperature
        current_temperature = current_temperature / self.number_devices
        current_time = time.time()
        temp_object = [current_time, current_temperature]
        self.temperatures.append(temp_object)
        for i in range(len(self.temperatures)):
            if current_time - self.temperatures[i][0] < 86400.:
                break
        self.temperatures = self.temperatures[i:]
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

class switch(object):
    def __init__(self, switch_device, ext_temp):
        self.switch_device = switch_device
        self.ext_temp = ext_temp
        self.low_temp_pattern = [[10000., 11000.], [20000., 21000.], [29000., 30000.], [35000., 36000.], \
                                 [40000., 41000.], [45000., 46000.], [50000., 51000.], [55000., 56000.], \
                                 [61000., 62000.], [70000., 71000.], [80000., 81000.]]
        self.high_temp_pattern = [[3000.,  4000.], [ 8000.,  9000.], [13000., 14000.], [18000., 19000.], \
                                 [26000., 27000.], [36000., 37000.], [46000., 47000.], [56000., 57000.], \
                                 [61000., 62000.], [69000., 70000.], [77000., 78000.], [83000., 84000.]]
        self.transition_temperature = 10.
        self.ventilator_on = False

    def ventilator_state_update(self):
        self.ext_temp.update_temperature()
        if self.ext_temp.max_temperature > self.transition_temperature:
            temp_pattern = self.high_temp_pattern
        else:
            temp_pattern = self.low_temp_pattern
        switch_on = False
        for interval in temp_pattern:
            if interval[0] < time.time()-self.ext_temp.min_temperature_time < interval[1]:
                switch_on = True
                break
        if self.switch_device.is_on() != switch_on:
            self.switch_device.toggle()


if __name__=="__main__":
    ccu = pmatic.CCU(address="http://192.168.0.51", credentials=("Admin", "xxx"), connect_timeout=5)
    for device in ccu.devices.query(device_name=u"HM-LC-Sw1-Pl-DN-R1 xxxx"):
        switch_device = device
    ext_temp = temperature_external(ccu)
    switch_object = switch(switch_device, ext_temp)

    while True:
        switch_object.ventilator_state_update()
        time.sleep(120)