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
    """Compute the current date and time.

    :return: Character string with current date and time information
    """
    return datetime.datetime.fromtimestamp(time.time())


def get_local_hour(params, timestamp):
    """
    Compute the number of hours passed since local midnight.

    Args:
        params: parameter object
        timestamp: Unix timestamp (seconds passed since Jan. 1st, 1970, 0:00 UTC)

    Returns: the number of hours since local midnight. Examples: 0. for midnight, 12. for local noon, 12.5 for
             half an hour after local noon.
    """
    return (timestamp / 3600. + params.utc_shift) % 24.


def look_up_device(params, ccu, dev_name):
    """Look up the device by its name. If two devices are found with the same name, print an error message and exit.

    Args:
        params: parameter object
        ccu: pmatic CCU data object
        dev_name: device name (utf-8 string)

    Returns: the device object

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


def print_output(output_string):
    """Print a text string to stdout, preceded by the current UTC date and time.

    Args:
        output_string: character string to be printed behind the UTC time info

    Returns: -

    """
    print datetime.datetime.fromtimestamp(time.time()), output_string