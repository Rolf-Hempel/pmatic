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

from miscellaneous import *


class sysvar_activities(object):
    """This class defines shutter setting activities controlled by system variables.

    This makes it possible to trigger activities from outside this program, e.g. by setting a system variable with
    a HomeMatic remote control unit.

    """

    def __init__(self, params, api):
        """
        Define the activities and their corresponding data structures.

        :param params: parameter object
        :param api: pmatic object which gives access to the JSON RPC Api of HomeMatic
        :return: -
        """
        self.api = api
        self.params = params
        self.suspend_shutter_activities = {"name": u'Keine Rolladenbewegungen', "active": False}
        self.suspend_sleeping_room = {"name": u'Keine RB Schlafzimmer', "active": False}
        self.ventilate_upper = {"name": u'Lueften Obergeschoss', "active": False, "setting": 1.,
                                "windows": [u'Schlafzimmer', u'Kinderzimmer', u'Badezimmer', u'Arbeitszimmer']}
        self.ventilate_lower = {"name": u'Lueften Erdgeschoss', "active": False, "setting": 1.,
                                "windows": [u'Wohnzimmer rechts', u'Küche rechts', u'Gäste-WC']}
        self.ventilate_kitchen = {"name": u'Lueften Kueche', "active": False, "setting": 1.,
                                  "windows": [u'Küche rechts', u'Gäste-WC']}
        self.ventilate_night = {"name": u'Lueften Nacht', "active": False, "setting": 1.,
                                "windows": [u'Schlafzimmer', u'Kinderzimmer', u'Badezimmer', u'Arbeitszimmer',
                                            u'Wohnzimmer rechts']}
        self.shutter_constant_25 = {"name": u'Rollaeden 25 Prozent', "active": False, "setting": 0.25,
                                    "windows": [u'Schlafzimmer', u'Kinderzimmer', u'Badezimmer', u'Arbeitszimmer',
                                                u'Wohnzimmer rechts', u'Wohnzimmer links', u'Küche rechts',
                                                u'Küche links', u'Gäste-WC', u'Terrassentür', u'Terrassenfenster']}
        self.shutter_constant_50 = {"name": u'Rollaeden 50 Prozent', "active": False, "setting": 0.5,
                                    "windows": [u'Schlafzimmer', u'Kinderzimmer', u'Badezimmer', u'Arbeitszimmer',
                                                u'Wohnzimmer rechts', u'Wohnzimmer links', u'Küche rechts',
                                                u'Küche links', u'Gäste-WC', u'Terrassentür', u'Terrassenfenster']}
        self.shutter_constant_100 = {"name": u'Rollaeden 100 Prozent', "active": False, "setting": 1.,
                                    "windows": [u'Schlafzimmer', u'Kinderzimmer', u'Badezimmer', u'Arbeitszimmer',
                                                u'Wohnzimmer rechts', u'Wohnzimmer links', u'Küche rechts',
                                                u'Küche links', u'Gäste-WC', u'Terrassentür', u'Terrassenfenster']}
        self.tv_evening = {"name": u'Fernsehabend', "active": False, "setting": 0.,
                           "windows": [u'Wohnzimmer rechts', u'Wohnzimmer links', u'Terrassentür', u'Terrassenfenster']}
        self.ventilate_until_morning = {"name": u'Lueften bis zum Morgen', "active": False}
        self.sysvar_ventilation_activities = [self.ventilate_upper, self.ventilate_lower,
                                              self.ventilate_kitchen, self.ventilate_night]
        self.sysvar_shutter_activities = [self.tv_evening, self.ventilate_upper, self.ventilate_lower,
                                          self.ventilate_kitchen, self.ventilate_night]
        self.constant_daytime_shutter_settings = [self.shutter_constant_25, self.shutter_constant_50,
                                                 self.shutter_constant_100]
        self.sysvars = {u'Keine Rolladenbewegungen': self.suspend_shutter_activities, u'Fernsehabend': self.tv_evening,
                        u'Lueften Obergeschoss': self.ventilate_upper, u'Lueften Erdgeschoss': self.ventilate_lower,
                        u'Lueften Kueche': self.ventilate_kitchen, u'Lueften Nacht': self.ventilate_night,
                        u'Keine RB Schlafzimmer': self.suspend_sleeping_room,
                        u'Lueften bis zum Morgen': self.ventilate_until_morning,
                        u'Rollaeden 25 Prozent': self.shutter_constant_25,
                        u'Rollaeden 50 Prozent': self.shutter_constant_50,
                        u'Rollaeden 100 Prozent': self.shutter_constant_100}

    def update(self):
        """
        Update the system variable settings
        :return: -
        """
        for sysvar_name, activity in self.sysvars.iteritems():
            # The pmatic api returns the values "true" and "false" as character strings instead of a boolean!
            new_value = self.api.sys_var_get_value_by_name(name=sysvar_name) == "true"
            if activity["active"] != new_value:
                if self.params.output_level > 1:
                    print_output("System variable " + sysvar_name + " has changed to " + str(new_value))
                activity["active"] = self.api.sys_var_get_value_by_name(name=sysvar_name) == "true"

    def sysvar_induced_setting(self, window_name):
        """
        For a window with name "window_name": Find out if it is included in an activity selected by an active system
        variable. For the first match, return the corresponding shutter setting.

        :param window_name:
        :return: sysvar-induced setting value, or None
        """
        for activity in self.sysvar_shutter_activities:
            if activity["active"] and window_name in activity["windows"]:
                return activity["setting"]
        return None

    def constant_daytime_setting(self, window_name):
        """
        For a window with name "window_name": Find out if a constant daytime setting is selected for it by an active
        system variable. For the first match, return the corresponding shutter setting. If there is no match,
        return None.

        :param window_name:
        :return: constant daytime setting value, or None
        """
        for activity in self.constant_daytime_shutter_settings:
            if activity["active"] and window_name in activity["windows"]:
                return activity["setting"]
        return None

    def shutter_activities_suspended(self):
        """
        If the boolean system variable "Keine Rolladenbewegungen" is set to "true", all shutter movements are suspended.
        :return: True if movements are suspended, otherwise False
        """
        return self.suspend_shutter_activities["active"]

    def reset_ventilation_in_the_morning(self):
        """
        If the boolean system variable "Lueften bis zum Morgen" is set to "true", all nocturnal ventilation actions
        are continued until the shutters are opened in the morning. At this point all ventilation actions are reset,
        and the system variable is reset to "False".
        :return: -
        """
        if self.ventilate_until_morning["active"]:
            if self.params.output_level > 1:
                print_output("Reset ventilation activities in the morning")
            for activity in self.sysvar_ventilation_activities:
                self.api.sys_var_set_float(name=activity["name"], value=False)
                activity["active"] = False
            self.api.sys_var_set_float(name=self.ventilate_until_morning["name"], value=False)
            self.ventilate_until_morning["active"] = False