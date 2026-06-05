import traceback
from miscellaneous import *

def a_function():
    a = 1.
    b = 0.
    c = a / b
    return c

def b_function():
    return a_function()

try:
    b_function()
except Exception as e:
    print_output("Error: " + str(e))
    print_output("", time_stamp=False)
    formatted_lines = traceback.format_exc().splitlines()
    for line in formatted_lines[:-1]:
        print_output(line, time_stamp=False)
    print_output("", time_stamp=False)