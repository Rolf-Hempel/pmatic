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
import os
import time

from parameters import parameters
from pmatic.exceptions import PMConnectionError


def set_time_zone():
    """
    Set the time zone to Berlin time


    :return: time zone string
    """
    timezone = "CET-1CEST,M3.5.0/2,M10.5.0/3"
    os.environ['TZ'] = timezone
    time.tzset()
    return timezone


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


def not_at_night(params):
    """
    Find out if the current time is outside the pre-defined night hours. Treat special cases Saturday and Sunday.

    :param params: parameter object
    :return: True for day time, otherwise False
    """
    lt = time.localtime()
    week_day = lt[6]
    civil_hour = lt[3] + lt[4] / 60.
    if 0 <= week_day <= 4:
        return params.ch_night_end < civil_hour < params.ch_night_begin
    # Special case Saturday:
    elif week_day == 5:
        return params.ch_night_end_saturday < civil_hour < params.ch_night_begin
    # Special case Sunday:
    else:
        return params.ch_night_end_sunday < civil_hour < params.ch_night_begin


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
        if params.output_level > 0:
            print_error_message(ccu, e)
    if len(devices) == 1:
        if params.output_level > 0:
            print dev_name
        return devices[0]
    elif len(devices) > 1:
        if params.output_level > 0:
            print " More than one device with name ", dev_name, " found, first one taken."
    else:
        if params.output_level > 0:
            print "*** Error: No device with name ", dev_name, " found, try again. ***"
        raise PMConnectionError()


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
        if params.output_level > 0:
            print_error_message(ccu, e)
    if len(devices) > 0:
        if params.output_level > 0:
            for device in devices:
                print device.name
        return devices
    else:
        if params.output_level > 0:
            print "*** Error: No device with type ", dev_type, " found, try again. ***"
        raise PMConnectionError()


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


def linear_regression(x, y):
    """
    Compute the linear regression parameters for given x and y vectors.

    :param x: Vector with abscissa values (length > 1)
    :param y: Vector with ordinate values (same length as x)
    :return: values for slope and axis intersection of the linear regression function y=a*x+b.
            For invalid input values, None is returned.
    """
    n = len(x)
    if n < 2 or len(y) != n:
        return None
    sumh = float(sum(y))
    sumt = float(sum(x))
    sumth = float(sum(x[i] * y[i] for i in range(n)))
    sumt2 = float(sum(x[i] ** 2 for i in range(n)))
    a = (sumth - sumt * sumh / n) / (sumt2 - (sumt ** 2) / n)
    b = (sumh - a * sumt) / n
    return a, b


def print_output(output_string):
    """
    Print a text string to stdout, preceded by the current UTC date and time

    :param output_string: character string to be printed behind the UTC time info
    :return: -
    """
    print datetime.datetime.fromtimestamp(time.time()), output_string


def print_error_message(ccu, exception_object):
    """
    For a PMException, parse the error message for the device address and look up that address in a dictionary with
    addresses and device names. If the address is found, print a readable error message including the device name.
    If no appropriate address is found in the error message, or if the address is not in the dictionary, print the
    error message as is.

    :param ccu: pmatic CCU data object
    :param exception_object: PMException object
    :return: -
    """
    err_string = str(exception_object)
    address_string = err_string[
                     err_string.index('address') + 12:err_string.index(u':', err_string.index('address') + 13)]

    struct = ccu.api.device_list_all_detail()
    for item in struct:
        if item[u'address'] == address_string:
            print_output('*** Error in accessing device "' + item[u'name'] + '" ***')
            return
    print_output(err_string)


if __name__ == "__main__":
    params = parameters("parameter_file")
    time_stamp = time.time()
    print "Date and time: ", date_and_time(), ", timestamp: ", time_stamp
    print "Current local hour: ", get_local_hour(params, time_stamp)
    print "Not at night: ", not_at_night(params)
