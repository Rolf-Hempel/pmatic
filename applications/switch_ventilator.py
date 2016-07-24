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

import pmatic
from miscellaneous import *


class switch_ventilator(object):
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

