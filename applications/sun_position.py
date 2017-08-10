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

from math import degrees, radians

from miscellaneous import *
from pmatic import utils


class sun_position(object):
    def __init__(self, params):
        self.params = params
        self.sun_is_up_last_changed = 0.
        self.lookahead_steps = int(self.params.sunlit_lookahead_time / self.params.main_loop_sleep_time) + 1
        self.time_last_updated = 0.

    def update_position(self):
        self.time_last_updated = time.time()
        self.sun_lookahead_positions = []
        for i in range(self.lookahead_steps):
            self.sun_lookahead_positions.append(self.get_sun_position(delta_t=i * self.params.main_loop_sleep_time))
        # for (azimuth, elevation) in self.sun_lookahead_positions:
        #     print_output("Sun position: Azimuth = " + str(degrees(azimuth)) +
        #                  ", Elevation = " + str(degrees(elevation)))
        self.azimuth, self.elevation = self.sun_lookahead_positions[0]
        if self.params.output_level > 2:
            print_output("Sun position: Azimuth = " + str(degrees(self.azimuth)) +
                         ", Elevation = " + str(degrees(self.elevation)))
        return self.azimuth, self.elevation

    def get_sun_position(self, delta_t=0.):
        # If a delta_t != 0. is specified, look up the sun position in delta_t seconds from now.
        return utils.sun_position(radians(self.params.longitude), radians(self.params.latitude),
                                  unix_secs=self.time_last_updated + delta_t)

    def look_up_position(self):
        return self.azimuth, self.elevation

    def sun_is_up(self, brightnesses):
        # If the sun is high enough, return True anyway
        if self.elevation > radians(self.params.sunrise_decision_width):
            self.last_sun_is_up = True
        # If the sun is low enough below the horizon, return False anyway
        elif self.elevation < -radians(self.params.sunrise_decision_width):
            self.last_sun_is_up = False
        # If the sun's elevation is close enough to the horizon, decide based on external brightness
        else:
            t = time.time()
            local_hour = get_local_hour(self.params, t)
            # Don't change back and forth in the presence of clouds
            if time.time() - self.sun_is_up_last_changed > self.params.sunrise_decision_interval:
                # Around sunrise test is the sky is already bright enough
                if local_hour < 12.:
                    if brightnesses.current_brightness_external > self.params.day_brightness_threshold:
                        self.last_sun_is_up = True
                        self.sun_is_up_last_changed = t
                    else:
                        self.last_sun_is_up = False
                # Around sunset test if the sky is already dim enough
                else:
                    if brightnesses.current_brightness_external < self.params.night_brightness_threshold:
                        self.last_sun_is_up = False
                        self.sun_is_up_last_changed = t
                    else:
                        self.last_sun_is_up = True
        return self.last_sun_is_up


if __name__ == "__main__":
    params = parameters("parameter_file")
    sun = sun_position(params)
    azimuth, elevation = sun.update_position()
