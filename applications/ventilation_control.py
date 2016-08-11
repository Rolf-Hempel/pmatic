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
from switch_ventilator import switch_ventilator
from temperature_humidity import temperature_humidity

ccu_parameter_file_name = "/etc/config/addons/pmatic/scripts/applications/ventilation_basement/parameter_file"
remote_parameter_file_name = "parameter_file"

if os.path.isfile(ccu_parameter_file_name):
    params = parameters(ccu_parameter_file_name)
    # For execution on CCU redirect stdout to a protocol file
    sys.stdout = codecs.open('/media/sd-mmcblk0/protocols/ventilation.txt', encoding='utf-8', mode='a')
    if params.output_level > 0:
        print ""
        print_output(
            "++++++++++++++++++++++++++++++++++ Start Local Execution on CCU +++++++++++++++++++++++++++++++++++++")
    ccu = pmatic.CCU()
else:
    params = parameters(remote_parameter_file_name)
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
temperature_device_external = look_up_device_by_name(params, ccu, u'Temperatur- und Feuchtesensor außen')
temperature_device_internal = look_up_device_by_name(params, ccu, u'Temperatur- und Feuchtesensor Gartenkeller')
switch_device = look_up_device_by_name(params, ccu, u"Steckdosenschalter Gartenkeller")

th = temperature_humidity(params, temperature_device_external, temperature_device_internal)
sw = switch_ventilator(params, switch_device)

# main loop
while True:
    if params.update_parameters():
        if params.output_level > 1:
            print "\nParameters have changed!"
            params.print_parameters()

    th.update_temperature_humidity()
    sw.ventilator_state_update(th.current_temperature_internal, th.current_temperature_external,
                               th.current_humidity_external, th.max_temperature, th.min_temperature_time,
                               th.max_temperature_time)

    time.sleep(params.main_loop_sleep_time)
