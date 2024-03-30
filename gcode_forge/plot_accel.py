
import matplotlib.pyplot as plt
import numpy as np

from acceleration import SCurveAcceleration

dt_s = 0.010
accel_dy_mmss = 10.0
ramp_time_s = 0.200
max_accel_mmss = 3000

profile = SCurveAcceleration(ramp_time_s, max_accel_mmss, dt_s, accel_dy_mmss)

import time
start = time.perf_counter()
accel, velocity, position = profile.calc(0, 100)
print(time.perf_counter() - start)

print('final velocity', velocity[-1])




fig, ax = plt.subplots()

time = np.arange(0, 100, dt_s)[:len(accel)]

ax.plot(time, accel, label='accel')
ax.plot(time, velocity, label='velocity')
ax.plot(time, position, label='position')

ax.legend()
plt.show()