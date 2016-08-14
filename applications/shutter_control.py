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
from math import radians, degrees

import pmatic
from miscellaneous import *
from parameters import parameters
from sun_position import sun_position


class window(object):
    """This class provides all functions to operate a window shutter.

    The parts of the sky which are visible from the window can be defined on initialization, as well as the parameters
    for the translation function between nominal and true shutter settings. During operation, manual interventions are
    recognized. In this case the shutter of the corresponding window is left untouched by the program until the shutter
    is opened completely manually. A test function which determines if the sun can currently illuminate the window is
    provieded.

    """

    def __init__(self, params, ccu, sun, window_name, room_name, shutter_name):
        """
        Store objects and names corresponding to this window on initialization

        :param params: parameter object
        :param ccu: pmatic CCU data object
        :param sun: object which stores parameters for computing the current position of the sun
        :param window_name: window name (utf-8 string)
        :param room_name: room name (utf-8 string)
        :param shutter_name: shutter name (utf-8 string)
        """
        self.params = params
        self.ccu = ccu
        self.sun = sun
        self.window_name = window_name
        self.room_name = room_name
        self.shutter_name = shutter_name
        self.shutter = look_up_device_by_name(params, ccu, shutter_name)
        self.shutter_last_setting = -1.
        self.shutter_manual_intervention_active = False
        self.open_spaces = []
        self.shutter_coef = [0., 1., 0.]

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

        :return: True, if sun is in an open sky patch. False, otherwise
        """
        sun_azimuth, sun_elevation = self.sun.Look_up_position()
        sunlit = False
        for ([azimuth_lower, azimuth_upper, elevation_lower, elevation_upper]) in self.open_spaces:
            if azimuth_lower <= sun_azimuth <= azimuth_upper and elevation_lower <= sun_elevation <= elevation_upper:
                sunlit = True
                break
        return sunlit

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

    def set_shutter(self, value):
        """
        Set the shutter to a given level: 0 for completely closed, 1 for completely opened shutter. Any value in between
        is possible.

        :param value: intended shutter setting
        :return: True, if shutter was set successfully; False otherwise
        """
        success = True
        if value < 0. or value > 1.:
            print_output("Error: Invalid shutter value " + str(value) + " specified.")
            success = False
        else:
            try:
                self.shutter_current_setting = self.shutter.blind.level
                time.sleep(self.params.lookup_sleep_time)
                # Test if the shutter has been operated manually since the last setting operation. In this case set
                # variable "self.shutter_manual_intervention_active" to True. This will inhibit shutter operations by
                # this program until the shutter is opened completely manually.
                if abs(self.shutter_current_setting - self.shutter_last_setting) > \
                        self.params.shutter_setting_tolerance and self.shutter_last_setting != -1.:
                    if self.shutter_current_setting == 1.:
                        if self.params.output_level > 1:
                            print_output("End of manual intervention for shutter " + self.shutter_name)
                        self.shutter_manual_intervention_active = False
                    else:
                        if self.params.output_level > 1:
                            print_output("Manual intervention for shutter " + self.shutter_name + " found, new level: "
                                         + str(self.shutter_current_setting))
                        self.shutter_manual_intervention_active = True
                self.shutter_last_setting = self.shutter_current_setting

                nominal_setting = self.true_to_nominal(value)
                # Test if current shutter setting differs from target value and no manual intervention is active
                if abs(nominal_setting - self.shutter_current_setting) > self.params.shutter_setting_tolerance and not \
                        self.shutter_manual_intervention_active:
                    if self.params.output_level > 1:
                        print_output("Setting shutter " + self.shutter_name + " to new level: " + str(value))
                    # Apply translation between intended and nominal shutter settings
                    success = self.shutter.blind.set_level(nominal_setting)
                    # After a shutter operation, wait for a pre-defined period in order to avoid radio interference
                    time.sleep(self.params.shutter_trigger_delay)
                    self.shutter_last_setting = nominal_setting
            except Exception as e:
                if self.params.output_level > 0:
                    print e
                success = False
        return success


class windows(object):
    """
    This class keeps a dictionary with all window objects, to be accessed via the window name. Collective operations
    to open and close all windows, or windows which satisfy a certain condition, are provided.

    """

    def __init__(self, params, ccu, sun):
        self.params = params
        self.ccu = ccu
        self.sun = sun
        self.window_dict = {}

        if self.params.output_level > 0:
            print "\nThe following shutter devices are used:"
        # Initialize all windows. Set open sky areas and coefficients for translating true to nominal shutter settings
        window_name = u'Schlafzimmer'
        w = window(self.params, self.ccu, self.sun, window_name, u'Schlafzimmer', u'Rolladenaktor Schlafzimmer')
        w.add_open_space(51., 76., 7., 90.)
        w.add_open_space(76., 116., 4., 90.)
        w.add_open_space(116., 136., 7., 50.)
        w.add_open_space(136., 156., 13., 50.)
        w.add_open_space(156., 171., 7., 50.)
        w.add_open_space(171., 191., 7., 35.)
        w.add_open_space(191., 216., 7., 20.)
        w.add_shutter_coef([-0.12959185, 0.86158566, 0.25446371])
        # Add the window object to the dictionary with all windows
        self.window_dict[window_name] = w

        window_name = u'Kinderzimmer'
        w = window(self.params, self.ccu, self.sun, window_name, u'Kinderzimmer', u'Rolladenaktor Kinderzimmer')
        w.add_open_space(231., 360., 0., 90.)
        w.add_shutter_coef([-0.26234962, 0.98880658, 0.24321233])
        self.window_dict[window_name] = w

        window_name = u'Arbeitszimmer'
        w = window(self.params, self.ccu, self.sun, window_name, u'Arbeitszimmer', u'Rolladenaktor Arbeitszimmer')
        w.add_open_space(231., 246., 2., 20.)
        w.add_open_space(246., 256, 2., 40.)
        w.add_open_space(256., 271., 2., 55.)
        w.add_open_space(271., 360., 2., 60.)
        w.add_shutter_coef([-0.26234962, 0.98880658, 0.24321233])
        self.window_dict[window_name] = w

        window_name = u'Badezimmer'
        w = window(self.params, self.ccu, self.sun, window_name, u'Badezimmer', u'Rolladenaktor Badezimmer')
        w.add_open_space(61., 78., 8., 27.)
        w.add_open_space(78., 146, 4., 55.)
        w.add_open_space(146., 166., 13., 57.)
        w.add_open_space(166., 201., 4., 55.)
        w.add_shutter_coef([-0.12959185, 0.86158566, 0.25446371])
        self.window_dict[window_name] = w

        window_name = u'Wohnzimmer rechts'
        w = window(self.params, self.ccu, self.sun, window_name, u'Wohnzimmer rechts',
                   u'Rolladenaktor Wohnzimmer rechts')
        w.add_open_space(231., 360., 2., 90.)
        w.add_shutter_coef([-0.19781835, 0.92476391, 0.255443])
        self.window_dict[window_name] = w

        window_name = u'Wohnzimmer links'
        w = window(self.params, self.ccu, self.sun, window_name, u'Wohnzimmer links',
                   u'Rolladenaktor Wohnzimmer links')
        w.add_open_space(231., 360., 2., 90.)
        w.add_shutter_coef([-0.19781835, 0.92476391, 0.255443])
        self.window_dict[window_name] = w

        window_name = u'Terrassentür'
        w = window(self.params, self.ccu, self.sun, window_name, u'Terrassentür',
                   u'Rolladenaktor Terrassentür')
        w.add_open_space(151., 181., 0., 33.)
        w.add_open_space(181., 191., 0., 38.)
        w.add_open_space(191., 241., 20., 38.)
        w.add_open_space(241., 246., 7., 37.)
        w.add_open_space(246., 293., 3., 40.)
        w.add_shutter_coef([-0.19527282, 0.94210207, 0.24104221])
        self.window_dict[window_name] = w

        window_name = u'Terrassenfenster'
        w = window(self.params, self.ccu, self.sun, window_name, u'Terrassenfenster',
                   u'Rolladenaktor Terrassenfenster')
        w.add_open_space(151., 181., 0., 33.)
        w.add_open_space(181., 191., 0., 38.)
        w.add_open_space(191., 241., 20., 38.)
        w.add_open_space(241., 246., 7., 37.)
        w.add_open_space(246., 293., 3., 40.)
        w.add_shutter_coef([-0.19527282, 0.94210207, 0.24104221])
        self.window_dict[window_name] = w

        window_name = u'Küche links'
        w = window(self.params, self.ccu, self.sun, window_name, u'Küche links',
                   u'Rolladenaktor Küche links')
        w.add_open_space(51., 79., 8., 90.)
        w.add_open_space(79., 106., 5., 90.)
        w.add_open_space(106., 136., 14., 90.)
        w.add_open_space(136., 171., 20., 90.)
        w.add_open_space(171., 211., 8., 90.)
        w.add_shutter_coef([-0.12244656, 0.89711513, 0.21811965])
        self.window_dict[window_name] = w

        window_name = u'Küche rechts'
        w = window(self.params, self.ccu, self.sun, window_name, u'Küche rechts',
                   u'Rolladenaktor Küche rechts')
        w.add_open_space(141., 156., 16., 90.)
        w.add_open_space(156., 206., 5., 90.)
        w.add_open_space(206., 231., 20., 90.)
        w.add_open_space(231., 266., 16., 30.)
        w.add_open_space(266., 276., 3., 25.)
        w.add_open_space(276., 291., 3., 19.)
        w.add_open_space(291., 301., 3., 13.)
        w.add_shutter_coef([-0.17358483, 0.91958752, 0.23608076])
        self.window_dict[window_name] = w

        window_name = u'Gäste-WC'
        w = window(self.params, self.ccu, self.sun, window_name, u'Gäste-WC',
                   u'Rolladenaktor Gäste-WC')
        w.add_open_space(51., 79., 8., 90.)
        w.add_open_space(79., 121., 5., 90.)
        w.add_open_space(121., 141., 14., 90.)
        w.add_open_space(141., 176., 18., 90.)
        w.add_open_space(176., 211., 7., 90.)
        w.add_shutter_coef([-0.20875883, 0.89494005, 0.28198548])
        self.window_dict[window_name] = w

        # Print a list of all windows
        if self.params.output_level > 0:
            print "\nWindows with shutter control:"
            for w in self.window_dict.values():
                print "Room: ", w.room_name, ", Window: ", w.window_name, ", Device: ", w.shutter_name

    def close_all_shutters(self):
        if self.params.output_level > 2:
            print_output("Closing all shutters")
        for window in self.window_dict.values():
            window.set_shutter(0.)

    def open_all_shutters(self):
        if self.params.output_level > 2:
            print_output("Opening all shutters")
        for window in self.window_dict.values():
            window.set_shutter(0.4)


if __name__ == "__main__":
    # Depending on whether the program is executed on the CCU2 itself or on a remote PC, the parameters are stored at
    # different locations.
    ccu_parameter_file_name = "/etc/config/addons/pmatic/scripts/applications/parameter_file"
    remote_parameter_file_name = "parameter_file"

    # Test if the CCU parameter file is found. In this case the program runs on the CCU2.
    if os.path.isfile(ccu_parameter_file_name):
        params = parameters(ccu_parameter_file_name)
        # For execution on CCU redirect stdout to a protocol file
        sys.stdout = codecs.open('/media/sd-mmcblk0/protocols/shutter_control.txt', encoding='utf-8', mode='a')
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

    # Create the object which stores parameters for computing the sun's location in the sky
    sun = sun_position(params)
    sun_twilight_threshold = radians(params.sun_twilight_threshold)

    # Create window dictionary and initialize parameters for all windows
    windows = windows(params, ccu, sun)

    # Main loop
    while True:
        # Read parameter file and check if since the last iteration parameters have changed
        if params.update_parameters():
            sun = sun_position(params)
            sun_twilight_threshold = radians(params.sun_twilight_threshold)
            if params.output_level > 1:
                print "\nParameters have changed!"
                params.print_parameters()
        # Compute the current sun position
        sun_azimuth, sun_elevation = sun.update_position()
        if params.output_level > 2:
            print_output("Sun position: Azimuth = " + str(degrees(sun_azimuth)) +
                         ", Elevation = " + str(degrees(sun_elevation)))
        # If the sun is below a certain elevation threshold, close all shutters, otherwise open them (if they are not
        # open yet.
        if sun_elevation < sun_twilight_threshold:
            windows.close_all_shutters()
        else:
            windows.open_all_shutters()
        # Add a delay before the next main loop iteration
        time.sleep(params.main_loop_sleep_time)
