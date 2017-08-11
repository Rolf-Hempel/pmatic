class interpolation(object):
    def __init__(self, window_name):
        self.window_name = window_name

    def linear_interpolation(self, profile, sun_azimuth):
        if sun_azimuth <= profile[0][0] or sun_azimuth > profile[-1][0]:
            print '*** Error: invalid profile for window ' + self.window_name + ' ***'
            return -1.
        for [azimuth, elevation] in profile:
            if azimuth < sun_azimuth:
                azimuth_left = azimuth
                elevation_left = elevation
            else:
                azimuth_right = azimuth
                elevation_right = elevation
                return (sun_azimuth - azimuth_left) / (azimuth_right - azimuth_left) * elevation_right + \
                       (azimuth_right - sun_azimuth) / (azimuth_right - azimuth_left) * elevation_left



if __name__ == "__main__":
    prof = []
    prof.append([25., 2.])
    prof.append([50., 4.])
    prof.append([75., 8.])
    prof.append([100., 16.])
    prof.append([125., 8.])
    prof.append([150., 6.])
    prof.append([175., 2.])

    inter = interpolation("Schlafzimmer")

    sun_az = 25.0001
    elevation = inter.linear_interpolation(prof, sun_az)
    print "azimuth: ", sun_az, ", elevation: ", elevation