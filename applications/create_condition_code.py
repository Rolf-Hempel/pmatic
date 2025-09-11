for temperature in ["very-hot-fcst", "hot-fcst", "very-hot", "hot", "normal", "cold"]:
    for brightness in ["very-bright", "normal", "dim"]:
        for sunlit in ["sunlit", "shade"]:
            variable = "shutter_" + temperature + "_" + brightness + "_" + sunlit
            print 'if "' + variable + '" in self.parameters.keys():\n\tself.shutter_condition["' + variable + \
                  '"] = float(self.parameters["' + variable + '"])\nelse:\n\tself.shutter_condition["' \
                  + variable + '"] = 0.00'

print ""

for temperature in ["very-hot-fcst", "hot-fcst", "very-hot", "hot", "normal", "cold"]:
    for brightness in ["very-bright", "normal", "dim"]:
        for sunlit in ["sunlit", "shade"]:
            variable = "shutter_" + temperature + "_" + brightness + "_" + sunlit
            print '"\\n' + variable + ': ", self.shutter_condition["' + variable + '"], \\'