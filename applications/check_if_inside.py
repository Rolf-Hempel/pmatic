def check_if_inside(local_hour):
    switch_on_local_hour = 0.5
    self_params_ventilation_switch_on_hours = 2.
    lb = switch_on_local_hour
    ub = switch_on_local_hour + self_params_ventilation_switch_on_hours
    x = local_hour
    if x-24. >= lb:
        x -= 24.
    if x+24. <= ub:
        x += 24.
    is_inside = lb <= x <= ub
    return is_inside

x = 0.
while x<=24.:
    print "x: ,", x, " is_inside: ", check_if_inside(x)
    x += 0.25