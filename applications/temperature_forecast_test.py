import codecs
import sys

import pmatic.api
from miscellaneous import *
from parameters import parameters
from temperature import temperature

if __name__ == "__main__":

    # Set the time zone to Berlin time.
    set_time_zone()

    # Depending on whether the program is executed on the CCU2 itself or on a remote PC, the parameters are stored at
    # different locations.
    ccu_parameter_file_name = "/etc/config/addons/pmatic/scripts/applications/parameter_file"
    remote_parameter_file_name = "/home/rolf/PycharmProjects/pmatic/applications/parameter_file"
    ccu_temperature_file_name = "/etc/config/addons/pmatic/scripts/applications/temperature_file"
    remote_temperature_file_name = "/home/rolf/PycharmProjects/pmatic/applications/temperature_file"

    # Test if the remote parameter file is found. In this case the program runs on a remote computer.
    if os.path.isfile(remote_parameter_file_name):
        params = parameters(remote_parameter_file_name)
        temperature_file_name = remote_temperature_file_name
        if params.output_level > 0:
            print_output("", time_stamp=False)
            print_output(
                "++++++++++++++++++++++++++++++++++ Start Remote Execution on PC +++++++++++++++++++++++++++++++++++++")
        ccu = pmatic.CCU(address=params.ccu_address, credentials=(params.user, params.password), connect_timeout=5)
        api = pmatic.api.init(address=params.ccu_address, credentials=(params.user, params.password))
    else:
        params = parameters(ccu_parameter_file_name)
        temperature_file_name = ccu_temperature_file_name
        # For execution on CCU redirect stdout to a protocol file
        sys.stdout = codecs.open('/media/sd-mmcblk0/protocols/home_control.txt', encoding='utf-8', mode='a')
        if params.output_level > 0:
            print_output("", time_stamp=False)
            print_output(
                "++++++++++++++++++++++++++++++++++ Start Local Execution on CCU +++++++++++++++++++++++++++++++++++++")
        ccu = pmatic.CCU()
        api = pmatic.api.init()

    if params.output_level > 0:
        params.print_parameters()

    # Create the object which keeps the current temperature and maximum/minimum values during the previous day
    temperatures = temperature(params, ccu, temperature_file_name)

    params.temperature_update_interval = 0

    temperatures.update()