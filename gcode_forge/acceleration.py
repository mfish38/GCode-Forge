
from functools import lru_cache


import numpy as np
from numpy import clip
import numpy.typing as npt

import scipy as sp
from scipy.integrate import cumulative_trapezoid




class AccelerationProfile:
    def __init__(self, ramp_mmss: npt.NDArray[np.float64], dt_s: float, accel_dy_mmss: float, const_accel_mmss: float):
        '''
        ramp_mmss
            Acceleration profile for ramping up acceleration from 0 to the constant acceleration value.

            At the end of the profile, const_accel_mmss will be used as long as needed, and then acceleration
            will be ramped down using a reversed version of the profile.

        dt_s
            Time between acceleration profile elements and the output acceleration and velocity elements.

        accel_dy_mmss
            This is used to tune max acceleration reached to more closely hit the target delta_mms.

            The initially calculated acceleration profile will be clipped repeatedly by this amount until
            the final velocity delta is just under the desired delta_mms.

            This allows more accuracy than is allowed by the ramp/const_accel_mms values in the given dx_mm spacing.
            It is also used to hit the desired velocity when the acceleration distance is less than 2 * the
            distance of the ramp profile.

        const_accel_mmss
            Constant acceleration that will be used between the acceleration ramp up and down.
        '''
        self.ramp_mmss = ramp_mmss
        self.dt_s = dt_s
        self.accel_dy_mmss = accel_dy_mmss
        self.const_accel_mmss = const_accel_mmss
        ramp_velocity = cumulative_trapezoid(ramp_mmss, dx=dt_s, initial=0)
        self.ramp_stop_now_velocity = ramp_velocity * 2
        self.final_velocity_after_ramps = self.ramp_stop_now_velocity[-1]
        self.places = None

    @lru_cache(1024)
    def _calc_abs_delta(self, delta_mms: float) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        '''
        delta_mms
            Delta change in mm/s. This must be positive.

        Returns (accel, velocity, position)
        '''
        ramp_stop_now_velocity = self.ramp_stop_now_velocity
        ramp_mmss = self.ramp_mmss
        const_accel_mmss = self.const_accel_mmss
        dt_s = self.dt_s
        accel_dy_mmss = self.accel_dy_mmss

        if self.final_velocity_after_ramps >= delta_mms:
            stop_mask = np.where(ramp_stop_now_velocity >= delta_mms)[0]
            stop_index = stop_mask[0]
            accel = np.r_[ramp_mmss[:stop_index], ramp_mmss[stop_index::-1]]

            reached_accel = ramp_mmss[stop_index]
        else:
            constant_accel_distance = (delta_mms - ramp_stop_now_velocity[-1]) / const_accel_mmss
            accel = np.r_[ramp_mmss, np.full(int(constant_accel_distance / dt_s), const_accel_mmss), ramp_mmss[::-1]]

            reached_accel = const_accel_mmss

        # clip until the final velocity is just less than the target
        # TODO: binary search across accel_dy sized chunks
        # TODO: clip or scale?
        while True:
            velocity = cumulative_trapezoid(accel, dx=dt_s, initial=0)
            final_velocity = velocity[-1]
            if final_velocity <= delta_mms:
                break

            reached_accel -= accel_dy_mmss
            accel = clip(accel, None, reached_accel)

        position = cumulative_trapezoid(velocity, dx=dt_s, initial=0)

        return accel, velocity, position

    def calc(self, from_mms: float, to_mms: float) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        delta_mms = to_mms - from_mms

        # Better lru_cache hit rate for slight loss in accuracy
        delta_mms = round(delta_mms, self.places)

        accel, velocity, position = self._calc_abs_delta(abs(delta_mms))

        if delta_mms <= 0:
            velocity = velocity[::-1]
            velocity = velocity + to_mms
        else:
            velocity = velocity + from_mms

        return accel, velocity, position




class SCurveAcceleration(AccelerationProfile):
    def __init__(self, ramp_time_s: float, max_accel_mmss: float, dt_s: float, accel_dy_mmss: float):
        ramp_s = np.arange(0, ramp_time_s + dt_s, dt_s)
        ramp_mmss = np.interp(
            ramp_s,
            [
                0,
                ramp_time_s,
            ],
            [
                0,
                max_accel_mmss,
            ]
        )
        super().__init__(ramp_mmss, dt_s, accel_dy_mmss, max_accel_mmss)

# import matplotlib.pyplot as plt

# dt_s = 0.010
# accel_dy_mmss = 10.0
# ramp_time_s = 0.100
# max_accel_mmss = 3000

# profile = SCurveAccelProfile(ramp_time_s, max_accel_mmss, dt_s, accel_dy_mmss)

# import time
# accel, velocity, position = profile.calc(200, 100)
# start = time.perf_counter()
# accel, velocity = profile.calc(100, 200)
# print(time.perf_counter() - start)
# print(np.stack((position, accel, velocity)))

# print('final velocity', velocity[-1])




# fig, ax = plt.subplots()

# time = np.arange(0, 100, dt_s)[:len(accel)]

# ax.plot(time, accel, label='accel')
# ax.plot(time, velocity, label='velocity')
# ax.plot(time, position, label='position')

# ax.legend()
# plt.show()