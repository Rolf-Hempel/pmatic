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
import sys
from math import radians
import time

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
        self.lower_profile = []
        self.upper_profile = []
        self.shutter_coef = [0., 1., 0.]
        self.last_sunlit_condition = "none"

        ccu_not_ready_yet = True
        while ccu_not_ready_yet:
            try:
                self.shutter = look_up_device_by_name(params, ccu, shutter_name)
                ccu_not_ready_yet = False
            except:
                time.sleep(params.main_loop_sleep_time)

    def add_lower_profile_point(self, base_azimuth, azimuth, elevation):
        """
        Add the azimuthal coordinates of a point on the horizon as seen from this window.

        :param base_azimuth: azimuth angle of the zero point for this window (in degrees)
        :param azimuth: azimuth angle of the point (in degrees)
        :param elevation: elevation angle of the point (in degrees)
        :return: -
        """
        self.lower_profile.append([radians(base_azimuth + azimuth), radians(elevation)])

    def add_upper_profile_point(self, base_azimuth, azimuth, elevation):
        """
        Add the azimuthal coordinates of a point on the upper free space boundary as seen from this window.

        :param base_azimuth: azimuth angle of the zero point for this window (in degrees)
        :param azimuth: azimuth angle of the point (in degrees)
        :param elevation: elevation angle of the point (in degrees)
        :return: -
        """
        self.upper_profile.append([radians(base_azimuth + azimuth), radians(elevation)])

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
        Test if the sun can potentially illuminate the window (without regarding clouds). If a change relative to the
        last call is detected, check if the new condition will not change again for a given number of seconds
        (specified with the parameter "sunlit_lookahead_time"). Only then the change takes effect.

        :return: "sunlit", if sun is in an open sky patch. "shade", otherwise
        """
        sun_azimuth, sun_elevation = self.sun.look_up_position()
        new_condition = self.sun_in_open_space(sun_azimuth, sun_elevation)
        if new_condition == self.last_sunlit_condition or self.last_sunlit_condition == "none":
            # No change is detected, or this is the first call.
            self.last_sunlit_condition = new_condition
            return new_condition
        for (sun_azimuth, sun_elevation) in self.sun.sun_lookahead_positions[1:]:
            if self.sun_in_open_space(sun_azimuth, sun_elevation) != new_condition:
                return self.last_sunlit_condition
        self.last_sunlit_condition = new_condition
        return new_condition

    def sun_in_open_space(self, sun_azimuth, sun_elevation):
        """
        Test if currently the sun at coordinates (sun_azimuth, sun_elevation) can potentially illuminate the window
        (without regarding clouds).

        :return: "sunlit", if sun is in an open sky patch. "shade", otherwise
        """

        if (self.linear_interpolation(self.lower_profile, sun_azimuth) <= sun_elevation
                <= self.linear_interpolation(self.upper_profile, sun_azimuth)):
            return "sunlit"
        else:
            return "shade"

    def linear_interpolation(self, profile, sun_azimuth):
        """
        Auxiliary routine: interpolate profile elevation linearly at azimuth position of the sun.

        :param profile: list with [azimuth,elevation] pairs which define the profile (horizon or upper space boundary)
        :param sun_azimuth: azimuth value for which the elevation is to be computed
        :return: interpolated elevation value, or -1 if the azimuth is out of range
        """

        # Check if azimuth is out of range:
        if sun_azimuth <= profile[0][0] or sun_azimuth > profile[-1][0]:
            print_output('*** Error: invalid profile for window ' + self.window_name + ' ***')
            return -1.
        for [azimuth, elevation] in profile:
            if azimuth < sun_azimuth:
                # Store point left of desired location.
                azimuth_left = azimuth
                elevation_left = elevation
            else:
                # Current point is the first to the right of desired location.
                azimuth_right = azimuth
                elevation_right = elevation
                return (sun_azimuth - azimuth_left) / (azimuth_right - azimuth_left) * elevation_right + \
                       (azimuth_right - sun_azimuth) / (azimuth_right - azimuth_left) * elevation_left

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

    def set_shutter(self, temperature_condition, brightness_condition, sun_is_up):
        """
        Set the shutter to a given level: 0 for completely closed, 1 for completely opened shutter. Any value in between
        is possible.

        :param value: intended shutter setting
        :param temperature_condition: temperature classification, either "cold" or "normal" or "hot"
        :param brightness_condition: brightness classification, either "dim" or "normal" or "very bright"
        :param sun_is_up: boolean: "True" for daytime, "False" otherwise
        :return: True, if shutter was set successfully; False otherwise
        """
        success = True
        end_of_manual_intervention = False

        sunlit_cond = self.test_sunlit()
        shutter_cond = "shutter_" + temperature_condition + "_" + brightness_condition + "_" + \
                            sunlit_cond
        value = self.params.shutter_condition[shutter_cond]

        # If for this window a constant daytime shutter setting is selected, use it. Otherwise take the value passed to
        # this function via the argument "value".
        true_setting = self.sysvar_act.constant_daytime_setting(self.window_name)

        # If true_setting is None, no constant daytime shutter setting is active.
        if true_setting == None:
            true_setting = value

        # If a constant daytime shutter setting is active for this window, look if the setting should
        # be different for windows in sunlight and in the shade. In the latter case, make the shutter
        # setting dependent of the temperature, but assume a very bright light environment.
        elif self.sysvar_act.light_shade_separate["active"]:
            if sunlit_cond != "sunlit":
                shutter_cond = "shutter_" + temperature_condition + "_very-bright_shade"
                true_setting = self.params.shutter_condition[shutter_cond]

        if true_setting < 0. or true_setting > 1. and self.params.output_level > 0:
            print_output("*** Error: Invalid shutter value " + str(true_setting) + " specified. ***")
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
                if (abs(nominal_setting - self.shutter_current_setting) > self.params.shutter_setting_tolerance and not
                            self.shutter_manual_intervention_active and (
                            not_at_night(self.params) or self.sysvar_act.changed)) or end_of_manual_intervention:
                    if self.params.output_level > 1:
                        print_output("Setting shutter " + self.shutter_name + " to new level: " + str(true_setting))
                    # Move the shutter
                    success = self.shutter.blind.set_level(nominal_setting)
                    # After a shutter operation, wait for a pre-defined period in order to avoid radio interference
                    time.sleep(self.params.shutter_trigger_delay)
                    self.shutter_last_setting = nominal_setting
            except Exception as e:
                if self.params.output_level > 0:
                    print_error_message(self.ccu, e)
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
        w.add_lower_profile_point(41., -41.,  8.5)
        w.add_lower_profile_point(41.,  20.,  8.5)
        w.add_lower_profile_point(41.,  38.,  8.0)
        w.add_lower_profile_point(41.,  40.,  4.5)
        w.add_lower_profile_point(41.,  80.,  4.5)
        w.add_lower_profile_point(41.,  88., 10.0)
        w.add_lower_profile_point(41.,  95.,  4.5)
        w.add_lower_profile_point(41., 115., 16.5)
        w.add_lower_profile_point(41., 125., 12.0)
        w.add_lower_profile_point(41., 135.,  5.5)
        w.add_lower_profile_point(41., 360.,  5.5)
        w.add_upper_profile_point(41., -41.,  8.4)
        w.add_upper_profile_point(41.,  20.,  8.5)
        w.add_upper_profile_point(41.,  48., 40.0)
        w.add_upper_profile_point(41.,  90., 57.0)
        w.add_upper_profile_point(41., 150., 49.0)
        w.add_upper_profile_point(41., 160., 47.0)
        w.add_upper_profile_point(41., 160.1, 5.4)
        w.add_upper_profile_point(41., 360.,  5.4)
        w.add_shutter_coef([-0.12959185, 0.86158566, 0.25446371])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Kinderzimmer'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Kinderzimmer',
                   u'Rolladenaktor Kinderzimmer')
        w.add_lower_profile_point(221., -221.,  6.0)
        w.add_lower_profile_point(221.,   10.,  6.0)
        w.add_lower_profile_point(221.,   60.,  2.0)
        w.add_lower_profile_point(221.,  170.,  2.0)
        w.add_upper_profile_point(221., -221.,  5.9)
        w.add_upper_profile_point(221.,   10.,  6.0)
        w.add_upper_profile_point(221.,   20., 45.0)
        w.add_upper_profile_point(221.,   60., 63.0)
        w.add_upper_profile_point(221.,  120., 54.0)
        w.add_upper_profile_point(221.,  170.,  2.0)
        w.add_shutter_coef([-0.26234962, 0.98880658, 0.24321233])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Arbeitszimmer'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Arbeitszimmer',
                   u'Rolladenaktor Arbeitszimmer')
        w.add_lower_profile_point(221., -221.,  2.0)
        w.add_lower_profile_point(221.,   10.,  2.0)
        w.add_lower_profile_point(221.,   60.,  0.0)
        w.add_lower_profile_point(221.,  170.,  2.0)
        w.add_upper_profile_point(221., -221.,  1.9)
        w.add_upper_profile_point(221.,  19.9,  1.9)
        w.add_upper_profile_point(221.,   20., 11.0)
        w.add_upper_profile_point(221.,   33., 37.0)
        w.add_upper_profile_point(221.,   80., 58.0)
        w.add_upper_profile_point(221.,  140., 55.0)
        w.add_upper_profile_point(221.,  170.,  2.0)

        w.add_shutter_coef([-0.26234962, 0.98880658, 0.24321233])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Schlafzimmer'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Schlafzimmer',
                   u'Rolladenaktor Schlafzimmer')
        w.add_lower_profile_point(41., -41.,  8.0)
        w.add_lower_profile_point(41.,  10.,  8.0)
        w.add_lower_profile_point(41.,  35.,  8.0)
        w.add_lower_profile_point(41.,  36.,  4.5)
        w.add_lower_profile_point(41.,  60.,  4.5)
        w.add_lower_profile_point(41.,  75.,  6.0)
        w.add_lower_profile_point(41.,  83., 10.0)
        w.add_lower_profile_point(41.,  89.,  5.0)
        w.add_lower_profile_point(41.,  95., 16.5)
        w.add_lower_profile_point(41., 120., 13.5)
        w.add_lower_profile_point(41., 128.,  6.5)
        w.add_lower_profile_point(41., 165.,  6.5)
        w.add_lower_profile_point(41., 360.,  6.5)
        w.add_upper_profile_point(41., -41.,  7.9)
        w.add_upper_profile_point(41.,  9.9,  7.9)
        w.add_upper_profile_point(41.,  10., 20.0)
        w.add_upper_profile_point(41.,  37., 55.0)
        w.add_upper_profile_point(41.,  83., 61.0)
        w.add_upper_profile_point(41., 153., 25.0)
        w.add_upper_profile_point(41., 165.,  6.5)
        w.add_upper_profile_point(41., 360.,  6.4)
        w.add_shutter_coef([-0.12959185, 0.86158566, 0.25446371])
        # Add the window object to the dictionary with all windows
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Gäste-WC'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Gäste-WC',
                   u'Rolladenaktor Gäste-WC')
        w.add_lower_profile_point(41., -41., 10.0)
        w.add_lower_profile_point(41.,  25., 10.0)
        w.add_lower_profile_point(41.,  35.,  9.5)
        w.add_lower_profile_point(41.,  38.,  4.0)
        w.add_lower_profile_point(41.,  62.,  5.0)
        w.add_lower_profile_point(41.,  80.,  6.5)
        w.add_lower_profile_point(41.,  89., 14.0)
        w.add_lower_profile_point(41., 102., 13.0)
        w.add_lower_profile_point(41., 108., 21.0)
        w.add_lower_profile_point(41., 135., 12.5)
        w.add_lower_profile_point(41., 136.,  6.5)
        w.add_lower_profile_point(41., 165.,  6.5)
        w.add_lower_profile_point(41., 360.,  6.5)
        w.add_upper_profile_point(41., -41.,  9.9)
        w.add_upper_profile_point(41., 24.9,  9.9)
        w.add_upper_profile_point(41.,  25., 43.0)
        w.add_upper_profile_point(41.,  75., 60.0)
        w.add_upper_profile_point(41., 135., 50.0)
        w.add_upper_profile_point(41., 165., 45.0)
        w.add_upper_profile_point(41., 165.1, 6.4)
        w.add_upper_profile_point(41., 360.,  6.4)
        w.add_shutter_coef([-0.20875883, 0.89494005, 0.28198548])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Küche links'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Küche',
                   u'Rolladenaktor Küche links')
        w.add_lower_profile_point(41., -41.,  8.5)
        w.add_lower_profile_point(41.,  10.,  8.5)
        w.add_lower_profile_point(41.,  35.,  9.0)
        w.add_lower_profile_point(41.,  36.,  4.0)
        w.add_lower_profile_point(41.,  55.,  5.0)
        w.add_lower_profile_point(41.,  70., 15.0)
        w.add_lower_profile_point(41.,  80., 14.0)
        w.add_lower_profile_point(41.,  90.,  8.5)
        w.add_lower_profile_point(41.,  97., 23.0)
        w.add_lower_profile_point(41., 120., 17.5)
        w.add_lower_profile_point(41., 128.,  8.0)
        w.add_lower_profile_point(41., 170.,  8.0)
        w.add_lower_profile_point(41., 360.,  8.0)
        w.add_upper_profile_point(41., -41.,  8.4)
        w.add_upper_profile_point(41.,  9.9,  8.4)
        w.add_upper_profile_point(41.,  10., 33.0)
        w.add_upper_profile_point(41.,  60., 60.0)
        w.add_upper_profile_point(41.,  90., 75.0)
        w.add_upper_profile_point(41., 125., 64.0)
        w.add_upper_profile_point(41., 170., 25.0)
        w.add_upper_profile_point(41., 170.1, 7.9)
        w.add_upper_profile_point(41., 360.,  7.9)
        w.add_shutter_coef([-0.12244656, 0.89711513, 0.21811965])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Küche rechts'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Küche',
                   u'Rolladenaktor Küche rechts')
        w.add_lower_profile_point(131., -131., 17.0)
        w.add_lower_profile_point(131.,   20., 17.0)
        w.add_lower_profile_point(131.,   27., 13.5)
        w.add_lower_profile_point(131.,   30., 10.0)
        w.add_lower_profile_point(131.,   67., 11.5)
        w.add_lower_profile_point(131.,   80., 19.5)
        w.add_lower_profile_point(131.,  120., 17.0)
        w.add_lower_profile_point(131.,  127., 10.0)
        w.add_lower_profile_point(131.,  128.,  3.0)
        w.add_lower_profile_point(131.,  160.,  3.0)
        w.add_lower_profile_point(131.,  360.,  3.0)
        w.add_upper_profile_point(131., -131., 16.9)
        w.add_upper_profile_point(131.,  19.9, 16.9)
        w.add_upper_profile_point(131.,   20., 33.0)
        w.add_upper_profile_point(131.,   35., 53.0)
        w.add_upper_profile_point(131.,   75., 62.0)
        w.add_upper_profile_point(131.,  140., 52.0)
        w.add_upper_profile_point(131.,  141., 27.0)
        w.add_upper_profile_point(131.,  160., 14.0)
        w.add_upper_profile_point(131., 160.1,  2.9)
        w.add_upper_profile_point(131.,  360.,  2.9)
        w.add_shutter_coef([-0.17358483, 0.91958752, 0.23608076])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Wohnzimmer links'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Wohnzimmer',
                   u'Rolladenaktor Wohnzimmer links')
        w.add_lower_profile_point(221., -221.,  2.0)
        w.add_lower_profile_point(221.,   13.,  2.0)
        w.add_lower_profile_point(221.,   58.,  2.0)
        w.add_lower_profile_point(221.,   65.,  8.5)
        w.add_lower_profile_point(221.,   74.,  2.0)
        w.add_lower_profile_point(221.,  360.,  2.0)
        w.add_upper_profile_point(221., -221.,  1.9)
        w.add_upper_profile_point(221.,  12.9,  1.9)
        w.add_upper_profile_point(221.,   13., 48.0)
        w.add_upper_profile_point(221.,   20., 80.0)
        w.add_upper_profile_point(221.,  170., 80.0)
        w.add_shutter_coef([-0.19781835, 0.92476391, 0.255443])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Wohnzimmer rechts'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Wohnzimmer',
                   u'Rolladenaktor Wohnzimmer rechts')
        w.add_lower_profile_point(221., -221., 2.0)
        w.add_lower_profile_point(221.,   13., 2.0)
        w.add_lower_profile_point(221.,   50., 2.0)
        w.add_lower_profile_point(221.,   58., 9.0)
        w.add_lower_profile_point(221.,   67., 2.0)
        w.add_lower_profile_point(221.,  360., 2.0)
        w.add_upper_profile_point(221., -221., 1.9)
        w.add_upper_profile_point(221.,  12.9, 1.9)
        w.add_upper_profile_point(221.,  13., 48.0)
        w.add_upper_profile_point(221.,  20., 80.0)
        w.add_upper_profile_point(221., 170., 80.0)
        w.add_shutter_coef([-0.19781835, 0.92476391, 0.255443])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Terrassentür'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Wohnzimmer',
                   u'Rolladenaktor Terrassentür')
        w.add_lower_profile_point(131., -131., 15.0)
        w.add_lower_profile_point(131.,   30., 15.0)
        w.add_lower_profile_point(131.,   60., 13.0)
        w.add_lower_profile_point(131.,   70., 19.0)
        w.add_lower_profile_point(131.,  117., 14.0)
        w.add_lower_profile_point(131.,  118.,  6.5)
        w.add_lower_profile_point(131.,  165.,  4.0)
        w.add_lower_profile_point(131.,  360.,  4.0)
        w.add_upper_profile_point(131., -131., 14.9)
        w.add_upper_profile_point(131.,  29.9, 14.9)
        w.add_upper_profile_point(131.,   30., 30.0)
        w.add_upper_profile_point(131.,   48., 30.0)
        w.add_upper_profile_point(131.,   62., 37.0)
        w.add_upper_profile_point(131.,   90., 40.0)
        w.add_upper_profile_point(131.,  118., 37.0)
        w.add_upper_profile_point(131.,  145., 25.0)
        w.add_upper_profile_point(131.,  150., 18.5)
        w.add_upper_profile_point(131.,  165., 30.0)
        w.add_upper_profile_point(131., 165.1,  3.9)
        w.add_upper_profile_point(131.,  360.,  3.9)
        # w.add_shutter_coef([-0.19527282, 0.94210207, 0.24104221])
        # Special case: do not open high windows too much
        w.add_shutter_coef([-0.72, 1.72, 0.])
        self.window_dict[window_name] = w
        self.window_list.append(window_name)

        window_name = u'Terrassenfenster'
        w = window(self.params, self.ccu, self.sysvar_act, self.sun, window_name, u'Wohnzimmer',
                   u'Rolladenaktor Terrassenfenster')
        w.add_lower_profile_point(131., -131., 14.5)
        w.add_lower_profile_point(131.,   20., 14.5)
        w.add_lower_profile_point(131.,   60., 15.0)
        w.add_lower_profile_point(131.,   68., 20.0)
        w.add_lower_profile_point(131.,  104., 20.0)
        w.add_lower_profile_point(131.,  110., 14.5)
        w.add_lower_profile_point(131.,  111.,  7.5)
        w.add_lower_profile_point(131.,  118.,  7.0)
        w.add_lower_profile_point(131.,  119.,  3.5)
        w.add_lower_profile_point(131.,  360.,  3.5)
        w.add_upper_profile_point(131., -131., 14.4)
        w.add_upper_profile_point(131.,  19.9, 14.4)
        w.add_upper_profile_point(131.,   20., 23.0)
        w.add_upper_profile_point(131.,   35., 27.0)
        w.add_upper_profile_point(131.,   62., 37.0)
        w.add_upper_profile_point(131.,   90., 40.0)
        w.add_upper_profile_point(131.,  118., 37.0)
        w.add_upper_profile_point(131.,  140., 26.5)
        w.add_upper_profile_point(131.,  160., 35.0)
        w.add_upper_profile_point(131., 160.1,  3.4)
        w.add_upper_profile_point(131.,  360.,  3.4)
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
                print_output('*** Warning: No brightness measurement available, using "normal" instead ***')
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
            # Update the system variable settings
            # time1 = time.time()
            self.sysvar_act.update()
            # time2 = time.time()
            # print 'sysvar_act.update function took %0.3f ms' % ((time2 - time1) * 1000.0)

            w = self.window_dict[wn]
            # Special case "Schlafzimmer": test system variable "Keine RB Schlafzimmer".
            if w.window_name != u'Schlafzimmer' or not self.sysvar_act.suspend_sleeping_room["active"]:
                w.set_shutter(temperature_condition, brightness_condition, sun_is_up)


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
