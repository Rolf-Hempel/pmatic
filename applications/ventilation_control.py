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
import os.path

import pmatic
from miscellaneous import *
from parameters import parameters
from temperature import temperature


class ventilation_control(object):
    def __init__(self, params, ccu):
        self.params = params
        if self.params.output_level > 0:
            print "\nThe following devices will be used for ventilation control:"
        ccu_not_ready_yet = True
        while ccu_not_ready_yet:
            try:
                self.switch_device = look_up_device_by_name(params, ccu, u"Steckdosenschalter Gartenkeller")
                self.temperature_device_internal = look_up_device_by_name(params, ccu,
                                                                          u'Temperatur- und Feuchtesensor Gartenkeller')
                self.current_temperature_internal = self.temperature_device_internal.temperature.value
                self.current_humidity_internal = self.temperature_device_internal.humidity.value / 100.
                ccu_not_ready_yet = False
            except:
                time.sleep(params.main_loop_sleep_time)
        self.last_updated = time.time()
        time.sleep(self.params.lookup_sleep_time)
        self.ventilation_active = False
        self.ventilation_switch_off_time = 0.

    def update_temperature_humidity_internal(self):
        if self.current_time - self.last_updated > self.params.temperature_update_interval:
            try:
                self.current_temperature_internal = self.temperature_device_internal.temperature.value
                self.current_humidity_internal = self.temperature_device_internal.humidity.value / 100.
                if self.params.output_level > 2:
                    print_output("Internal temperature: " + str(self.current_temperature_internal) +
                                 ", humidity: " + str(self.current_humidity_internal))
            except Exception as e:
                if self.params.output_level > 0:
                    print_output(repr(e))
            time.sleep(self.params.lookup_sleep_time)

    def optimal_ventilation_local_hour(self, temperatures):
        if self.current_temperature_internal > self.params.ventilation_transition_temperature:
            if temperatures.min_forecast_temperature != None:
                return temperatures.min_forecast_temperature_local_hour
            else:
                return temperatures.temp_dict["min_temperature_local_hour"]
        else:
            if temperatures.max_forecast_temperature != None:
                return temperatures.max_forecast_temperature_local_hour
            else:
                return temperatures.temp_dict["max_temperature_local_hour"]

    def status_update(self, temperatures):
        self.current_time = time.time()
        if self.ventilation_active:
            if self.current_time - self.ventilation_switch_on_time > self.params.ventilation_switch_on_hours * 3600.:
                try:
                    self.switch_device.switch_off()
                    if self.params.output_level > 2:
                        print_output("Ventilator switched off")
                    self.ventilation_switch_off_time = self.current_time
                    self.ventilation_active = False
                except Exception as e:
                    if self.params.output_level > 0:
                        print_output(repr(e))
                time.sleep(self.params.lookup_sleep_time)
        elif self.current_time - self.ventilation_switch_off_time > self.params.ventilation_min_idle_hours * 3600.:
            temperatures.update()
            self.update_temperature_humidity_internal()
            switch_on_local_hour = self.optimal_ventilation_local_hour(
                temperatures) - self.params.ventilation_switch_on_hours / 2.
            if temperatures.current_temperature_external <= self.params.ventilation_max_temperature and \
                            temperatures.dew_point < self.current_temperature_internal and \
                                    switch_on_local_hour <= get_local_hour(self.params, self.current_time) <= \
                                    switch_on_local_hour + self.params.ventilation_switch_on_hours:
                try:
                    self.switch_device.switch_on()
                    if self.params.output_level > 2:
                        print_output("Ventilator switched on")
                    self.ventilation_switch_on_time = self.current_time
                    self.ventilation_active = True
                except Exception as e:
                    if self.params.output_level > 0:
                        print_output(repr(e))
                time.sleep(self.params.lookup_sleep_time)


if __name__ == "__main__":

    ccu_parameter_file_name = "/etc/config/addons/pmatic/scripts/applications/parameter_file"
    remote_parameter_file_name = "/home/rolf/Pycharm-Projects/pmatic/applications/parameter_file"
    ccu_temperature_file_name = "/etc/config/addons/pmatic/scripts/applications/temperature_file"
    remote_temperature_file_name = "/home/rolf/Pycharm-Projects/pmatic/applications/temperature_file"

    if os.path.isfile(ccu_parameter_file_name):
        params = parameters(ccu_parameter_file_name)
        temperature_file_name = ccu_temperature_file_name
        # For execution on CCU redirect stdout to a protocol file
        sys.stdout = codecs.open('/media/sd-mmcblk0/protocols/ventilation.txt', encoding='utf-8', mode='a')
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

    ventilation = ventilation_control(params, ccu)
    temperatures = temperature(params, ccu, temperature_file_name)

    # Update temperature measurements and server forecast info at every call.
    params.temperature_update_interval = 0.

    # main loop
    while True:
        if params.update_parameters():
            if params.output_level > 1:
                print "\nParameters have changed!"
                params.print_parameters()

        ventilation.status_update(temperatures)

        time.sleep(params.main_loop_sleep_time)
