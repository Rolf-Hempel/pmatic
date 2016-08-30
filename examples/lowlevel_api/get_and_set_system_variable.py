#!/usr/bin/env python
# encoding: utf-8
#
# pmatic - Python API for Homematic. Easy to use.
# Copyright (C) 2016 Lars Michelsen <lm@larsmichelsen.com>
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

import pmatic.api

# Set a Homematic system vatiable and read its value

API = pmatic.api.init(
     address="http://192.168.0.51",
     credentials=("rolf", "Px9820rH"))

# API = pmatic.api.init()

print API.sys_var_get_all()

# print API.sys_var_get_value(id=u'40')

print ""

API.sys_var_set_float(name=u'Lueften Obergeschoss', value=1.)

print API.sys_var_get_value_by_name(name=u'Lueften Obergeschoss')


API.close()

