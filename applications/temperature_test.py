from parameters import parameters


class temperature(object):
    """
    This class keeps a persistent list of temperature measurements and statistical values on temperature minima and
    maxima. When a new measurement is available, the statistics are updated and the new data are stored in a file.
    After a program interruption, the file is read on program restart.

    """

    def __init__(self, params):
        self.params = params

        # No previously stored data available, initialize a new temperature dictionary
        self.temp_dict = {}
        self.temp_dict["temperatures"] = []
        self.temp_dict["temperatures_forecast"] = []
        self.temp_dict["last_updated"] = 0.
        self.temp_dict["minmax_time_updated"] = 0.
        self.temp_dict["min_temperature"] = params.min_temperature
        self.temp_dict["min_temperature_time"] = params.min_temperature_time
        self.temp_dict["max_temperature"] = params.max_temperature
        self.temp_dict["max_temperature_time"] = params.max_temperature_time
        self.current_temperature_external = (self.temp_dict["min_temperature"] + self.temp_dict["max_temperature"]) / 2.

    def temperature_condition(self, temperature_forecast):
        """
        Compare the current and maximum temperatures with predefined threshold values. For the characterization
        "very-hot" and "hot" both the current temperature and the maximum forecast temperature (or, if not available,
        the maximum temperature of the previous day) are used. The temperature is called "cold" if the maximum
        temperature of the previous day was below a certain threshold.

        :return: character string which characterizes the current temperature situation
        """

        if self.current_temperature_external > self.params.current_temperature_very_hot:
            return "very-hot"
        elif self.params.current_temperature_hot < self.current_temperature_external <= \
                self.params.current_temperature_very_hot:
            if temperature_forecast is None and self.temp_dict[
                "max_temperature"] > self.params.max_temperature_very_hot:
                return "very-hot"
            elif temperature_forecast is not None and temperature_forecast > self.params.max_temperature_very_hot:
                return "very-hot"
            else:
                return "hot"
        elif temperature_forecast is None:
            if max(self.current_temperature_external,
                   self.temp_dict["max_temperature"]) > self.params.max_temperature_hot:
                return "hot"
            elif max(self.current_temperature_external,
                     self.temp_dict["max_temperature"]) < self.params.max_temperature_cold:
                return "cold"
            else:
                return "normal"
        else:
            if temperature_forecast > self.params.max_temperature_very_hot:
                return "very-hot-fcst"
            elif temperature_forecast > self.params.max_temperature_hot:
                return "hot-fcst"
            elif temperature_forecast < self.params.max_temperature_cold:
                return "cold"
            else:
                return "normal"


if __name__ == "__main__":
    params = parameters("parameter_file")
    temp_object = temperature(params)

    print "params.current_temperature_hot: ", params.current_temperature_hot, ", params.current_temperature_very_hot: ", \
        params.current_temperature_very_hot, "\nparams.max_temperature_cold: ", params.max_temperature_cold, \
        ", params.max_temperature_hot: ", params.max_temperature_hot, ", params.max_temperature_very-hot: ", \
        params.max_temperature_very_hot

    temp_object.current_temperature_external = 21.
    temp_object.temp_dict["max_temperature"] = 12.
    temperature_forecast = 12.

    print "\ncurrent_temperature_external: ", temp_object.current_temperature_external, \
        ', temp_dict["max_temperature"]: ', temp_object.temp_dict["max_temperature"], ", temperature_forecast: ", \
        temperature_forecast

    print "\ntemperature condition: ", temp_object.temperature_condition(temperature_forecast)
