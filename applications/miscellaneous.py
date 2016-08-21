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

import datetime
import sys
import time


def date_and_time():
    """
    Compute the current date and time

    :return: Character string with current date and time information
    """
    return datetime.datetime.fromtimestamp(time.time())


def get_local_hour(params, timestamp):
    """
    Compute the number of hours passed since local midnight

    :param params: parameter object
    :param timestamp: Unix timestamp (seconds passed since Jan. 1st, 1970, 0:00 UTC)
    :return: the number of hours since local midnight. Examples: 0. for midnight, 12. for local noon, 12.5 for
             half an hour after local noon.
    """
    return (timestamp / 3600. + params.utc_shift) % 24.


def look_up_device_by_name(params, ccu, dev_name):
    """
    Look up the device by its name. If several devices are found with the same name, the first one is taken.

    :param params: parameter object
    :param ccu: pmatic CCU data object
    :param dev_name: device name (utf-8 string)
    :return: the device object
    """
    devices = {}
    try:
        devices = ccu.devices.query(device_name=dev_name)._devices.values()
    except Exception as e:
        print e
    if len(devices) == 1:
        if params.output_level > 0:
            print dev_name
        return devices[0]
    elif len(devices) > 1:
        print " More than one device with name ", dev_name, " found, first one taken."
    else:
        print " Error: No device with name ", dev_name, " found, execution halted."
        sys.exit(1)


def look_up_devices_by_type(params, ccu, dev_type):
    """
    Look up all devices with a given type. A list of devices is returned,

    :param params: parameter object
    :param ccu: pmatic CCU data object
    :param dev_type: device type (utf-8 string)
    :return: a list with the devices found
    """
    devices = []
    try:
        devices = ccu.devices.query(device_type=[dev_type])._devices.values()
    except Exception as e:
        print e
    if len(devices) > 0:
        if params.output_level > 0:
            for device in devices:
                print device.name
        return devices
    else:
        print " Error: No device with type ", dev_type, " found, execution halted."
        sys.exit(1)

def median(numeric_list):
    """
    Compute the median value in a list of arithmetic data.

    :param numeric_list: list of arithmetic values
    :return: median value of the list
    """
    lst = sorted(numeric_list)
    if len(lst) < 1:
        return None
    if len(lst) % 2 == 1:
        return lst[((len(lst) + 1) / 2) - 1]
    else:
        return float(sum(lst[(len(lst) / 2) - 1:(len(lst) / 2) + 1])) / 2.0


def print_output(output_string):
    """
    Print a text string to stdout, preceded by the current UTC date and time

    :param output_string: character string to be printed behind the UTC time info
    :return: -
    """
    print datetime.datetime.fromtimestamp(time.time()), output_string
