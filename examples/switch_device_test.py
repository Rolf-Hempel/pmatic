import codecs
import imp
import os.path
import sys
import time

import pmatic

ccu_parameter_file_name = "/etc/config/addons/pmatic/scripts/examples/parameter_file"
remote_parameter_file_name = "parameter_file"

if os.path.isfile(ccu_parameter_file_name):
    par = imp.load_source('parameters',
                          '/etc/config/addons/pmatic/scripts/applications/ventilation_basement/parameters.py')
    mis = imp.load_source('miscellaneous',
                          '/etc/config/addons/pmatic/scripts/applications/ventilation_basement/miscellaneous.py')

    params = par.parameters(ccu_parameter_file_name)
    # For execution on CCU redirect stdout to a protocol file
    sys.stdout = codecs.open('/media/sd-mmcblk0/protocols/switch_device_test.txt', encoding='utf-8', mode='a')
    if params.output_level > 0:
        print ""
        mis.print_output(
            "++++++++++++++++++++++++++++++++++ Start Local Execution on CCU +++++++++++++++++++++++++++++++++++++")
    ccu = pmatic.CCU()
else:
    par = imp.load_source('parameters', '/home/rolf/Pycharm-Projects/pmatic/applications/parameters.py')
    mis = imp.load_source('miscellaneous', '/home/rolf/Pycharm-Projects/pmatic/applications/miscellaneous.py')

    params = par.parameters(remote_parameter_file_name)
    if params.output_level > 0:
        print ""
        mis.print_output(
            "++++++++++++++++++++++++++++++++++ Start Remote Execution on PC +++++++++++++++++++++++++++++++++++++")
    ccu = pmatic.CCU(address=params.ccu_address, credentials=(params.user, params.password), connect_timeout=5)

if params.output_level > 1:
    params.print_parameters()

# Look up device for ventilator switching
if params.output_level > 0:
    print ""
    mis.print_output("Device used:")

switch_device = mis.look_up_device_by_name(params, ccu, u"Steckdosenschalter Wohnzimmer")

# main loop
while True:
    if params.update_parameters():
        if params.output_level > 1:
            print "\nParameters have changed!"
            params.print_parameters()

    try:
        if switch_device.is_on:
            if params.output_level > 1:
                mis.print_output(" Switching " + switch_device.name + " off")
            switch_device.switch_off()
        else:
            if params.output_level > 1:
                mis.print_output(" Switching " + switch_device.name + " on")
            switch_device.switch_on()
    except Exception as e:
        mis.print_error_message(ccu, e)

    time.sleep(params.main_loop_sleep_time)
