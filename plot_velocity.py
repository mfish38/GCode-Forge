
import matplotlib.pyplot as plt
import numpy as np

slow_distance_mm = 0.5
slow_speed_mms = 40
accel_step_distance_mm = 0.5
threshold_angle = 140
min_segment_length_mm = 0.05

target_speed_mms = 100

accel_exponent = 1.8
accel_scale_y = 1.0
accel_scale_x = 1.5

distance = np.linspace(0, 20, 100)
feed_rate_mms = np.clip(
    slow_speed_mms + ((distance * accel_scale_x) ** accel_exponent * accel_scale_y),
    None,
    target_speed_mms
)

fig, ax = plt.subplots()
ax.plot(distance, feed_rate_mms)

plt.show()