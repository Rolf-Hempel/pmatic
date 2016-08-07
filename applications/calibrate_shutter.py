import numpy as np


def nominal_to_true(c, setting_nominal):
    return c[0] * setting_nominal ** 2 + c[1] * setting_nominal + c[2]

def compute_coef(window_name, prn, heights, total_height):
    print "\n", "computing coefficients for window ", window_name, "\nNominal settings: ", prn
    prw = heights / total_height
    print "True settings: ", prw

    array = np.ndarray(shape=(3, 3), dtype=float)
    array[:, 0] = prw ** 2
    array[:, 1] = prw
    array[:, 2] = 1.
    # print "array: ", array, "\n"

    coef = np.linalg.solve(array, prn)
    print "coef: ", coef
    # print "\nTranslation from true to nominal settings:"

    # for i in range(11):
    #     setting_nominal = float(i)*0.1
    #     print "true: ", setting_nominal, ", nominal: ", nominal_to_true(coef, setting_nominal)

    # print "\nTest if coefficients match measurements:"
    # for i in range(3):
    #     print "true: ", prw[i], ", nominal: ", nominal_to_true(coef, prw[i])

    return coef

prn = np.array([0.3, 0.6, 0.9])

total_height = 1200.
heights = np.array([70., 485., 1033.])
coef = compute_coef("Arbeitszimmer", prn, heights, total_height)