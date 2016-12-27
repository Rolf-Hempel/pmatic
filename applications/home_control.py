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

import pmatic.api
from brightness import brightness
from miscellaneous import *
from parameters import parameters
from shutter_control import windows
from sun_position import sun_position
from system_variables import sysvar_activities
from temperature import temperature
from ventilation_control import ventilation_control

#
# This is the main control program for all smart home applications. Depending on whether the program is run on the CCU2
# or on a remote computer, it sets the file names for input and protocol files (for remote execution, protocol output
# is directed to stdout.) accordingly.
#
# Next, all control objects are created and initialized.
#
# Finally, the (infinite) main loop is started. First, parameter changes are detected. This gives the user a way to
# change parameters without interrupting the program. Then all objects are updated, and periodic activities (such as
# adjusting the shutters) are started. At the end of the main loop, a wait period is inserted to limit the CPU load.
#

if __name__ == "__main__":


    # Depending on whether the program is executed on the CCU2 itself or on a remote PC, the parameters are stored at
    # different locations.
    ccu_parameter_file_name = "/etc/config/addons/pmatic/scripts/applications/parameter_file"
    remote_parameter_file_name = "/home/rolf/Pycharm-Projects/pmatic/applications/parameter_file"
    ccu_temperature_file_name = "/etc/config/addons/pmatic/scripts/applications/temperature_file"
    remote_temperature_file_name = "/home/rolf/Pycharm-Projects/pmatic/applications/temperature_file"

    # Test if the remote parameter file is found. In this case the program runs on a remote computer.
    if os.path.isfile(remote_parameter_file_name):
        params = parameters(remote_parameter_file_name)
        temperature_file_name = remote_temperature_file_name
        if params.output_level > 0:
            print ""
            print_output(
                "++++++++++++++++++++++++++++++++++ Start Remote Execution on PC +++++++++++++++++++++++++++++++++++++")
        ccu = pmatic.CCU(address=params.ccu_address, credentials=(params.user, params.password), connect_timeout=5)
        api = pmatic.api.init(address=params.ccu_address, credentials=(params.user, params.password))
    else:
        params = parameters(ccu_parameter_file_name)
        temperature_file_name = ccu_temperature_file_name
        # For execution on CCU redirect stdout to a protocol file
        sys.stdout = codecs.open('/media/sd-mmcblk0/protocols/home_control.txt', encoding='utf-8', mode='a')
        if params.output_level > 0:
            print ""
            print_output(
                "++++++++++++++++++++++++++++++++++ Start Local Execution on CCU +++++++++++++++++++++++++++++++++++++")
        ccu = pmatic.CCU()
        api = pmatic.api.init()

    if params.output_level > 0:
        params.print_parameters()

    # Create the object which stores parameters for computing the sun's location in the sky
    sun = sun_position(params)

    # Create the object which defines shutter setting activities controlled by system variables
    sysvar_act = sysvar_activities(params, api)

    # Create window dictionary and initialize parameters for all windows
    windows = windows(params, ccu, sysvar_act, sun)

    # Create the object which keeps the current temperature and maximum/minimum values during the previous day
    temperatures = temperature(params, ccu, temperature_file_name)

    # Create the object which looks up the current brightness level and holds the maximum value during the last hour
    brightnesses = brightness(params, ccu)

    # Create the object which switches the ventilator in the basement on and off
    ventilation = ventilation_control(params, ccu)

    # Check battery-powered devices for low battery:
    device_with_low_battery = False
    for device in ccu.devices:
        if device.is_battery_low:
            if not device_with_low_battery:
                print ""
                print_output(
                    "++++++++++++++++++++++++++++++++++ Devices with low battery: ++++++++++++++++++++++++++++++++++++++++")
                device_with_low_battery = True
            print_output(device.name)

    if device_with_low_battery:
        print_output(
            "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    else:
        print ""
        print_output("All battery-powered devices are fine.")
    print ""

    # Main loop
    while True:
        # Read parameter file, check if since the last iteration parameters have changed.
        # If parameters have changed, create a new sun object. Otherwise just update sun position.
        if params.update_parameters():
            if params.output_level > 0:
                print ""
                print_output("Parameters have changed!")
                params.print_parameters()
                print ""
            # Reset time stamp for last test for sunrise/sunset. This is necessary because conditions might have
            # changed if, for example, the geographic position is changed.
            sun.sun_is_up_last_changed = 0.
        # Update sun position
        sun.update_position()
        # Update the temperature info
        temperatures.update()
        # Update the brightness info
        brightnesses.update()
        # Update the system variable setting
        sysvar_act.update()
        # Set all shutters corresponding to the actual temperature and brightness conditions.
        windows.adjust_all_shutters(temperatures, brightnesses)
        # Look if the ventilator in the basement has to be switched on or off.
        ventilation.status_update(temperatures)
        # Add a delay before the next main loop iteration
        time.sleep(params.main_loop_sleep_time)
