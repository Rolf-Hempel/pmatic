import numpy as np


def nominal_to_true(c, setting_nominal):
    return c[0] * setting_nominal ** 2 + c[1] * setting_nominal + c[2]

prn = np.array([0.3, 0.6, 0.9])
print "Nominal settings: ", prn, "\n"

total_height = 1200.
heights = np.array([70., 485., 1033.])
prw = heights / total_height
print "True settings: ", prw, "\n"

array = np.ndarray(shape=(3, 3), dtype=float)
array[:, 0] = prw ** 2
array[:, 1] = prw
array[:, 2] = 1.
print "array: ", array, "\n"

coef = np.linalg.solve(array, prn)
print "coef: ", coef, "\n\nTranslation from true to nominal settings:"

for i in range(11):
    setting_nominal = float(i)*0.1
    print "true: ", setting_nominal, ", nominal: ", nominal_to_true(coef, setting_nominal)

print "\nTest if coefficients match measurements:"
for i in range(3):
    print "true: ", prw[i], ", nominal: ", nominal_to_true(coef, prw[i])