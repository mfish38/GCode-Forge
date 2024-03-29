
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import scipy as sp

slow_distance_mm = 0.5
slow_speed_mms = 40
accel_step_distance_mm = 0.5
threshold_angle = 140
min_segment_length_mm = 0.05

target_speed_mms = 100

fig, ax = plt.subplots()

# accel_exponent = 3
# accel_scale_y = 1
# accel_scale_x = 1

# distance = np.linspace(0, 10, 50)
# feed_rate_mms = np.clip(
#     slow_speed_mms + ((distance * accel_scale_x) ** accel_exponent * accel_scale_y),
#     None,
#     target_speed_mms
# )
# accel = np.diff(feed_rate_mms)

# # ax.plot(distance, feed_rate_mms, label='a_velocity')
# # ax.plot(distance[1:], accel, label='a_accel')


# accel_exponent = 4
# accel_scale_y = 1
# accel_scale_x = 0.5

# distance = np.linspace(0, 10, 50)
# feed_rate_mms = np.clip(
#     slow_speed_mms + ((distance * accel_scale_x) ** accel_exponent * accel_scale_y),
#     None,
#     target_speed_mms
# )
# accel = np.diff(feed_rate_mms)

# ax.plot(distance, feed_rate_mms, label='b_velocity')
# ax.plot(distance[1:], accel, label='b_accel')


# linear
# accel = np.interp(
#     distance,
#     [
#         0,
#         3,
#         3,
#         6,
#         6
#     ],
#     [
#         4,
#         4,
#         0,
#         0,
#         -4
#     ]
# )


# todo: calculate how long to reach the desired speed

# todo instead to make generic calc as integrating up what speed we would be at if we stopped now and ramped down
#     this is just double the current speed as profile is identical mirror regardless of shape
#     this does not work for higher order as its too late

#     iterative solver?
#     way to integrate from both ends even though don't know where end is yet, will know once meet in the middle?
#     have integral of profile double it for ramp up and ramp down
#     simply find on the doubled profile where we meete critera, start at top and if not enough add in constant accel region which is just box as calculated below
# stop as soon as hit target


# TODO: memoize for various target velocity abs delta from start to end

def calc_velocity_profile(delta_mms: float, ramp_mmss: npt.NDArray[np.float64], dx_mm: float, accel_dy_mm: float, const_accel_mmss: float) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    '''
    delta_mms
        Delta change in mm/s. This must be positive. Simply multiply the output by -1 for de-acceleration.

    ramp_mmss
        Acceleration profile for ramping up acceleration from 0 to the constant acceleration value.

        At the end of the profile, const_accel_mmss will be used as long as needed, and then acceleration
        will be ramped down using a reversed version of the profile.

    dx_mm
        Distance between acceleration profile elements and the output acceleration and velocity elements.

    accel_dy_mm
        This is used to tune max acceleration reached to more closely hit the target delta_mms.

        The initially calculated acceleration profile will be clipped repeatedly by this amount until
        the final velocity delta is just under the desired delta_mms.

        This allows more accuracy than is allowed by the ramp/const_accel_mms values in the given dx_mm spacing.
        It is also used to hit the desired velocity when the acceleration distance is less than 2 * the
        distance of the ramp profile.

    const_accel_mmss
        Constant acceleration that will be used between the acceleration ramp up and down.

    Returns (accel, velocity)
    '''
    if delta_mms <= 0:
        raise Exception('delta_mms must be >= 0')

    ramp_velocity = sp.integrate.cumulative_trapezoid(ramp_mmss, dx=dx_mm, initial=0)
    ramp_stop_now_velocity = ramp_velocity * 2
    final_velocity_after_ramps = ramp_stop_now_velocity[-1]

    if final_velocity_after_ramps >= delta_mms:
        stop_mask = np.where(ramp_stop_now_velocity >= delta_mms)[0]
        stop_index = stop_mask[0]
        accel = np.r_[ramp_mmss[:stop_index], ramp_mmss[stop_index::-1]]

        reached_accel = ramp_mmss[stop_index]
    else:
        constant_accel_distance = (delta_mms - ramp_stop_now_velocity[-1]) / const_accel_mmss
        accel = np.r_[ramp_mmss, np.full(int(constant_accel_distance / dx_mm), ramp_stop_now_velocity[-1]), ramp_mmss[::-1]]

        reached_accel = const_accel_mmss

    # clip until the final velocity is just less than the target
    # TODO: binary search across accel_dy sized chunks
    # TODO: clip or scale?
    while True:
        velocity = sp.integrate.cumulative_trapezoid(accel, dx=dx_mm, initial=0)
        final_velocity = velocity[-1]
        if final_velocity <= delta_mms:
            break

        reached_accel -= accel_dy_mm
        accel = np.clip(accel, None, reached_accel)

    return accel, velocity

delta_mms = 58
dx = 0.2
accel_dy = 0.1
ramp_distance = 1
const_accel = 100

ramp_x = np.arange(0, ramp_distance + dx, dx)
ramp = np.interp(
    ramp_x,
    [
        0,
        ramp_distance,
    ],
    [
        0,
        const_accel,
    ]
)
accel, velocity = calc_velocity_profile(delta_mms, ramp, dx, accel_dy, const_accel)

print(velocity[-1])




# ramp_area = 0.5 * ramp_distance * max_accel
# if target <= ramp_area * 2:

#     print(target / (ramp_area * 2) * ramp_distance)
#     raise Exception('oh now')
# else:
#     constant_accel_distance = (target - ramp_area * 2) / max_accel

#     accel = np.interp(
#         distance,
#         [
#             0,
#             ramp_distance,
#             ramp_distance + constant_accel_distance,
#             ramp_distance + constant_accel_distance + ramp_distance,
#         ],
#         [
#             0,
#             max_accel,
#             max_accel,
#             0,
#         ]
#     )

# velocity = sp.integrate.cumulative_trapezoid(accel, dx=dx)
# velocity = np.trapz(accel, dx=dx)
# accel = np.diff(velocity)
# position = np.cumsum(velocity)

distance = np.arange(0, 10, dx)[:len(accel)]


ax.plot(distance, accel, label='accel')
ax.plot(distance, velocity, label='velocity')
# ax.plot(distance, position, label='position')



















ax.legend()
plt.show()