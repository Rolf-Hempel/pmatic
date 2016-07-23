import json


class parameters(object):
    def __init__(self):
        self.parameters = {}
        self.update_parameters()

    def update_parameters(self):
        self.parameters_old = self.parameters
        # with open("/etc/config/addons/pmatic/scripts/applications/ventilation_basement/parameter_file", "r") as parameter_file:
        with open("parameter_file", "r") as parameter_file:
            self.parameters = json.load(parameter_file)
        if self.test_for_changes():
            if "hostname" in self.parameters.keys():
                self.hostname = self.parameters["hostname"]
            else:
                self.hostname = "homematic-ccu2"
            if "ccu_address" in self.parameters.keys():
                self.ccu_address = self.parameters["ccu_address"]
            else:
                self.ccu_address = "192.168.0.51"
            if "user" in self.parameters.keys():
                self.user = self.parameters["user"]
            else:
                self.user = "rolf"
            if "password" in self.parameters.keys():
                self.password = self.parameters["password"]
            if "main_loop_sleep_time" in self.parameters.keys():
                self.main_loop_sleep_time = float(self.parameters["main_loop_sleep_time"])
            else:
                self.main_loop_sleep_time = 121.
            if "output_level" in self.parameters.keys():
                self.output_level = int(self.parameters["output_level"])
            else:
                self.output_level = 0
            if "longitude" in self.parameters.keys():
                self.longitude = float(self.parameters["longitude"])
            else:
                self.longitude = 7.9
            if "min_temperature_time" in self.parameters.keys():
                self.min_temperature_time = float(self.parameters["min_temperature_time"])
            else:
                self.min_temperature_time = 10800.
            if "max_temperature_time" in self.parameters.keys():
                self.max_temperature_time = float(self.parameters["max_temperature_time"])
            else:
                self.max_temperature_time = 39600.
            if "transition_temperature" in self.parameters.keys():
                self.transition_temperature = float(self.parameters["transition_temperature"])
            else:
                self.transition_temperature = 5.
            return True
        else:
            return False

    def test_for_changes(self):
        set_1 = set(self.parameters.iteritems())
        set_2 = set(self.parameters_old.iteritems())
        len(set_1.difference(set_2))
        return (len(set_1.difference(set_2)) | len(set_2.difference(set_1)))

    def print_parameters(self):
        print "\nParameters:", "\nhostname: ", self.hostname, "\nCCU address: ", self.ccu_address, "\nuser: ", \
            self.user, "\npassword: ", self.password, "\nmain_loop_sleep_time: ", self.main_loop_sleep_time, \
            "\noutput_level: ", self.output_level, "\nlongitude: ", self.longitude, "\nmin_temperature_time: ", \
            self.min_temperature_time, "\nmax_temperature_time: ", self.max_temperature_time, \
            "\ntransition_temperature: ", self.transition_temperature


if __name__ == "__main__":
    a = {"hostname": "Vega", "CCU address": "192.168.0.51", "user": "rolf", "password": "Px9820rH"}
    print "Parameters explicitly set in file:", a
    with open("parameter_file", 'w') as f:
        json.dump(a, f)

    params = parameters()

    params.print_parameters()

    a = {"hostname": "Vega", "CCU address": "192.168.0.51", "user": "rolf", "password": "Px9820rH"}
    print "\nParameters explicitly set in file:", a
    with open("parameter_file", 'w') as f:
        json.dump(a, f)

    if params.update_parameters():
        print "\nParameters have changed!"
        params.print_parameters()
    else:
        print "\nParameters are identical!"
