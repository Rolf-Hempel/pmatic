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
from math import radians

import pmatic.api
from brightness import brightness
from miscellaneous import *
from parameters import parameters
from sun_position import sun_position
from system_variables import sysvar_activities
from temperature import temperature


class window(object):
    """This class provides all functions to operate a window shutter.

    The parts of the sky which are visible from the window can be defined on initialization, as well as the parameters
    for the translation function between nominal and true shutter settings. During operation, manual interventions are
    recognized. In this case the shutter of the corresponding window is left untouched by the program until the shutter
    is opened completely manually. A test function which determines if the sun can currently illuminate the window is
    provieded.

    """

    def __init__(self, params, ccu, sysvar_act, sun, window_name, room_name, shutter_name):
        """
        Store objects and names corresponding to this window on initialization

        :param params: parameter object
        :param ccu: pmatic CCU data object
        :param sysvar_act: object with shutter setting activities controlled by system variables
        :param sun: object which stores parameters for computing the current position of the sun
        :param window_name: window name (utf-8 string)
        :param room_name: room name (utf-8 string)
        :param shutter_name: shutter name (utf-8 string)
        """
        self.params = params
        self.ccu = ccu
        self.sysvar_act = sysvar_act
        self.sun = sun
        self.window_name = window_name
        self.room_name = room_name
        self.shutter_name = shutter_name
        self.shutter_last_setting = -1.
        self.shutter_manual_intervention_active = False
        self.open_spaces = []
        self.shutter_coef = [0., 1., 0.]

        ccu_not_ready_yet = True
        while ccu_not_ready_yet:
            try:
                self.shutter = look_up_device_by_name(params, ccu, shutter_name)
                ccu_not_ready_yet = False
            except:
                time.sleep(params.main_loop_sleep_time)

    def add_open_space(self, azimuth_lower, azimuth_upper, elevation_lower, elevation_upper):
        """
        Add a rectangular patch of sky which is visible from this window. The complete patch of sky visible from this
        window can be composed of an arbitrary number of such rectangles.

        :param azimuth_lower: lower bound of rectangle in azimuth
        :param azimuth_upper: upper bound of rectangle in azimuth
        :param elevation_lower: lower bound of rectangle in elevation
        :param elevation_upper: upper bound of rectangle in elevation
        :return: -
        """
        self.open_spaces.append([radians(azimuth_lower), radians(azimuth_upper), \
                                 radians(elevation_lower), radians(elevation_upper)])

    def add_shutter_coef(self, coef):
        """
        Store the coefficients of a quadratic function which translates intended (true) shutter settings into nominal
        settings to be given to the pmatic shutter control function. The function is defined as:
            setting_nominal = coef[0] * setting_true**2 + coef[1]*setting_true + coef[2]
        The translation takes place in method "true_to_nominal".

        :param coef: list with function parameters
        :return: -
        """
        self.shutter_coef = coef

    def test_sunlit(self):
        """
        Test if currently the sun can potentially illuminate the window (without regarding clouds).

        :return: "sunlit", if sun is in an open sky patch. "shade", otherwise
        """
        sun_azimuth, sun_elevation = self.sun.look_up_position()
        sunlit_condition = "shade"
        for ([azimuth_lower, azimuth_upper, elevation_lower, elevation_upper]) in self.open_spaces:
            if azimuth_lower <= sun_azimuth <= azimuth_upper and elevation_lower <= sun_elevation <= elevation_upper:
                sunlit_condition = "sunlit"
                break
        return sunlit_condition

    def true_to_nominal(self, setting_true):
        """
        Translate intended (true) shutter settings into nominal settings to be given to the pmatic shutter control
        function. For a definition refer to method add_shutter_coef.

        :param setting_true: intended shutter setting. 0 for closed, 1 for completely opened shutter.
        :return: nominal setting to be passed to the pmatic shutter operation function.
        """

        # Test if shutter is to be opened or closed completely
        if setting_true == 1.:
            return 1.
        elif setting_true == 0.:
            return 0.
        else:
            # For intermediate settings apply translation function
            return max(0.,
                       min(1., self.shutter_coef[0] * setting_true ** 2 + self.shutter_coef[1] * setting_true +
                           self.shutter_coef[2]))

    def set_shutter(self, value, sun_is_up):
        """
        Set the shutter to a given level: 0 for completely closed, 1 for completely opened shutter. Any value in between
        is possible.

        :param value: intended shutter setting
        :return: True, if shutter was set successfully; False otherwise
        """
        success = True
        end_of_manual_intervention = False

        # If for this window a constant daytime shutter setting is selected, use it. Otherwise take the value passed to
        # this function via the argument "value".
        true_setting = self.sysvar_act.constant_daytime_setting(self.window_name)
        if true_setting == None:
            true_setting = value

        if true_setting < 0. or true_setting > 1.:
            print_output("Error: Invalid shutter value " + str(true_setting) + " specified.")
            success = False
        else:
            try:
                self.shutter_current_setting = self.shutter.blind.level
                time.sleep(self.params.lookup_sleep_time)
                # Check if for this window a setting has been selected via a system variable
                sysvar_induced_setting = self.sysvar_act.sysvar_induced_setting(self.window_name)
                if sysvar_induced_setting != None:
                    # A sysvar-induced setting overrides (and resets) a manual intervention
                    true_setting = sysvar_induced_setting
                    self.shutter_manual_intervention_active = False
                else:
                    # Test if the shutter has been operated manually since the last setting operation. In this case set
                    # variable "self.shutter_manual_intervention_active" to True. This will inhibit shutter operations by
                    # this program until the shutter is opened completely manually.
                    if abs(self.shutter_current_setting - self.shutter_last_setting) > \
                            self.params.shutter_setting_tolerance and self.shutter_last_setting != -1.:
                        if abs(self.shutter_current_setting - 1.) <= self.params.shutter_setting_tolerance:
                            if self.params.output_level > 1:
                                print_output("End of manual intervention for shutter " + self.shutter_name)
                            end_of_manual_intervention = True
                            self.shutter_manual_intervention_active = False
                        else:
                            if self.params.output_level > 1:
                                print_output(
                                    "Manual intervention for shutter " + self.shutter_name + " found, new level: "
                                    + str(self.shutter_current_setting))
                            self.shutter_manual_intervention_active = True
                    self.shutter_last_setting = self.shutter_current_setting

                    # If the sun is below the threshold value, close the shutter (if no sysvar-induced setting is
                    # active, and if there is no manual intervention)
                    if not sun_is_up:
                        true_setting = 0.

                # Apply translation between intended and nominal shutter settings
                nominal_setting = self.true_to_nominal(true_setting)
                # Test if current shutter setting differs from target value and no manual intervention is active
                if abs(nominal_setting - self.shutter_current_setting) > self.params.shutter_setting_tolerance and not \
                        self.shutter_manual_intervention_active and not not_at_night(self.params) or \
                        end_of_manual_intervention:
                    if self.params.output_level > 1:
                        print_output("Setting shutter " + self.shutter_name + " to new level: " + str(true_setting))
                    # Move the shutter
                    success = self.shutter.blind.set_level(nominal_setting)
                    # After a shutter operation, wait for a pre-defined period in order to avoid radio interference
                    time.sleep(self.params.shutter_trigger_delay)
                    self.shutter_last_setting = nominal_setting
            except Exception as e:
                if self.params.output_level > 0:
                    print_output(repr(e))
                success = False
        return success


class windows(object):
    """
    This class keeps a dictionary with all window objects, to be accessed via the window name. Collective operations
    to open and close all windows, or windows which satisfy a certain condition, are provided.

    """

    def __init__(self, params, ccu, sysvar_act, sun):
        self.params = params
        self.ccu = ccu
        self.sysvar_act = sysvar_act
        self.sun = sun
        self.window_dict = {}
        self.window_list = []

        if self.params.output_level > 0:
            print "\nThe following shutter devices are used:"
        # Initialize all windows. Set open sky areas and coefficients for translating true to nominal shutter settings

        window_name = u'Badezimmer'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Badezimmer',
                   u'Rolladenaktor Badezimmer')
        w.add_open_space(61., 78., 8., 27.)
        w.add_open_space(78., 146, 4., 55.)
        w.add_open_space(146., 166., 13., 57.)
        w.add_open_space(166., 201., 4., 55.)
        w.add_shutter_coef([-0.12959185, 0.86158566, 0.25446371])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Kinderzimmer'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Kinderzimmer',
                   u'Rolladenaktor Kinderzimmer')
        w.add_open_space(231., 360., 0., 90.)
        w.add_shutter_coef([-0.26234962, 0.98880658, 0.24321233])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Arbeitszimmer'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Arbeitszimmer',
                   u'Rolladenaktor Arbeitszimmer')
        w.add_open_space(231., 246., 2., 20.)
        w.add_open_space(246., 256, 2., 40.)
        w.add_open_space(256., 271., 2., 55.)
        w.add_open_space(271., 360., 2., 60.)
        w.add_shutter_coef([-0.26234962, 0.98880658, 0.24321233])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Schlafzimmer'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Schlafzimmer',
                   u'Rolladenaktor Schlafzimmer')
        w.add_open_space(51., 76., 7., 90.)
        w.add_open_space(76., 116., 4., 90.)
        w.add_open_space(116., 136., 7., 50.)
        w.add_open_space(136., 156., 13., 50.)
        w.add_open_space(156., 175., 7., 50.)
        w.add_open_space(175., 191., 7., 35.)
        w.add_open_space(191., 216., 7., 20.)
        w.add_shutter_coef([-0.12959185, 0.86158566, 0.25446371])
        # Add the window object to the dictionary with all windows
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Gäste-WC'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Gäste-WC',
                   u'Rolladenaktor Gäste-WC')
        w.add_open_space(51., 79., 8., 90.)
        w.add_open_space(79., 121., 5., 90.)
        w.add_open_space(121., 141., 14., 90.)
        w.add_open_space(141., 176., 18., 90.)
        w.add_open_space(176., 211., 7., 90.)
        w.add_shutter_coef([-0.20875883, 0.89494005, 0.28198548])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Küche links'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Küche',
                   u'Rolladenaktor Küche links')
        w.add_open_space(51., 79., 8., 90.)
        w.add_open_space(79., 106., 5., 90.)
        w.add_open_space(106., 136., 14., 90.)
        w.add_open_space(136., 171., 20., 90.)
        w.add_open_space(171., 211., 8., 90.)
        w.add_shutter_coef([-0.12244656, 0.89711513, 0.21811965])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Küche rechts'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Küche',
                   u'Rolladenaktor Küche rechts')
        w.add_open_space(141., 156., 16., 35.)
        w.add_open_space(156., 206., 5., 90.)
        w.add_open_space(206., 255., 20., 90.)
        w.add_open_space(255., 261., 3., 90.)
        w.add_open_space(261., 266., 3., 30.)
        w.add_open_space(266., 276., 3., 25.)
        w.add_open_space(276., 291., 3., 19.)
        w.add_open_space(291., 301., 3., 13.)
        w.add_shutter_coef([-0.17358483, 0.91958752, 0.23608076])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Wohnzimmer rechts'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Wohnzimmer',
                   u'Rolladenaktor Wohnzimmer rechts')
        w.add_open_space(231., 360., 2., 90.)
        w.add_shutter_coef([-0.19781835, 0.92476391, 0.255443])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Wohnzimmer links'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Wohnzimmer',
                   u'Rolladenaktor Wohnzimmer links')
        w.add_open_space(231., 360., 2., 90.)
        w.add_shutter_coef([-0.19781835, 0.92476391, 0.255443])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Terrassentür'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Wohnzimmer',
                   u'Rolladenaktor Terrassentür')
        w.add_open_space(151., 181., 0., 33.)
        w.add_open_space(181., 191., 0., 40.)
        w.add_open_space(191., 241., 20., 41.)
        w.add_open_space(241., 246., 7., 39.)
        w.add_open_space(246., 293., 3., 40.)
        # w.add_shutter_coef([-0.19527282, 0.94210207, 0.24104221])
        # Special case: do not open high windows too much
        w.add_shutter_coef([-0.72, 1.72, 0.])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Terrassenfenster'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Wohnzimmer',
                   u'Rolladenaktor Terrassenfenster')
        w.add_open_space(151., 181., 0., 33.)
        w.add_open_space(181., 191., 0., 40.)
        w.add_open_space(191., 241., 20., 41.)
        w.add_open_space(241., 246., 7., 39.)
        w.add_open_space(246., 293., 3., 40.)
        # w.add_shutter_coef([-0.19527282, 0.94210207, 0.24104221])
        # Special case: do not open high windows too much
        w.add_shutter_coef([-0.72, 1.72, 0.])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        # Print a list of all windows
        if self.params.output_level > 0:
            print "\nWindows with shutter control:"
            for wn in self.window_list:
                print "Room: ", self.window_dict[wn].room_name, ", Window: ", self.window_dict[wn].window_name, \
                    ", Device: ", self.window_dict[wn].shutter_name

    def adjust_all_shutters(self, temperatures, brightnesses):
        # Don't move shutters if shutter activities are suspended or if at night.
        if self.sysvar_act.shutter_activities_suspended():
            return
        temperature_condition = temperatures.temperature_condition()
        brightness_condition = brightnesses.brightness_condition()
        # Treat special case: List of brightness values truncated, and at the same time brightness device unavailable
        if brightness_condition == "no_measurement_available":
            if self.params.output_level > 2:
                print_output('Warning: No brightness measurement available, using "normal" instead')
            brightness_condition = "normal"
        if self.params.output_level > 2:
            print_output(
                "temperature condition: " + temperature_condition + ", brightness condition: " + brightness_condition)
        # If "sun_is_up" is False, shutters are to be closed for the night.
        sun_is_up = self.sun.sun_is_up(brightnesses)
        # Reset nocturnal ventilation activities the first time the sun is above the threshold.
        if sun_is_up:
            self.sysvar_act.reset_ventilation_in_the_morning()
        # For each window set the shutter according to lighting and temperature conditions.
        for wn in self.window_list:
            w = self.window_dict[wn]
            # Special case "Schlafzimmer": test system variable "Keine RB Schlafzimmer".
            if w.window_name != u'Schlafzimmer' or not self.sysvar_act.suspend_sleeping_room["active"]:
                sunlit_condition = w.test_sunlit()
                shutter_condition = "shutter_" + temperature_condition + "_" + brightness_condition + "_" + \
                                    sunlit_condition
                w.set_shutter(self.params.shutter_condition[shutter_condition], sun_is_up)


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
        # Wait for CCU startup to be completed
        # time.sleep(10.)
        params = parameters(ccu_parameter_file_name)
        temperature_file_name = ccu_temperature_file_name
        # For execution on CCU redirect stdout to a protocol file
        sys.stdout = codecs.open('/media/sd-mmcblk0/protocols/shutter_control.txt', encoding='utf-8', mode='a')
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
    # If "temperatures" and "brightnesses" are created, the temperature and brightness devices could be accessed.

    # Main loop
    while True:
        # Read parameter file, check if since the last iteration parameters have changed.
        # If parameters have changed, create a new sun object. Otherwise just update sun position.
        if params.update_parameters():
            if params.output_level > 0:
                print_output("\nParameters have changed!")
                params.print_parameters()
            # Reset time stamp for last test for sunrise/sunset.
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
        # Add a delay before the next main loop iteration
        time.sleep(params.main_loop_sleep_time)
