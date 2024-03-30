
import math

import numpy as np

from ..parser import GCodeFile, Line
from ..edit_utils import split_distance_back, split_distance_forward, next_continuous_move, apply_forward, apply_backward
from ..acceleration import SCurveAcceleration

def calc_junction_speed(max_accel_mmss, deviation, cos_theta, desired_feed_mms):
    # https://onehossshay.wordpress.com/2011/09/24/improving_grbl_cornering_algorithm/

    # If cos_theta is -1 then the angle of the junction is 180 deg and the following math would
    # divide by zero.
    if cos_theta <= math.nextafter(-1, 0):
        return desired_feed_mms

    sin_half_theta = math.sqrt((1 - cos_theta) / 2)
    r = deviation * (sin_half_theta / (1 - sin_half_theta))
    v_junction = math.sqrt(max_accel_mmss * r)

    return min(v_junction, desired_feed_mms)

def accelerate_backward(line: Line, from_mms: float, min_segment_length_mm: float, profile: SCurveAcceleration):
    accel, velocity, position = profile.calc(from_mms, line.annotation.desired_feed_mms)

    line.params['F'] = line.annotation.desired_feed_mms * 60

    current_start = line
    for dx, set_velocity in zip(np.diff(position), velocity[1:]):
        slow_cut = split_distance_back(current_start, dx, min_segment_length_mm)
        if not slow_cut:
            break

        def set_speed(line, set_velocity):
            if line.is_move:
                if 'F' in line.params:
                    current_line_feed_mms = line.params['F'] / 60
                    if current_line_feed_mms <= set_velocity:
                        return True

                line.params['F'] = set_velocity * 60
        stop = apply_backward(current_start, slow_cut, set_speed, set_velocity)
        if stop:
            break

        current_start = slow_cut
        if set_velocity >= current_start.annotation.desired_feed_mms:
            break

def accelerate_forward(line: Line, from_mms: float, min_segment_length_mm: float, profile: SCurveAcceleration):
    accel, velocity, position = profile.calc(from_mms, line.annotation.desired_feed_mms)

    slow_cut = None
    current_start = line
    first = True
    for dx, set_velocity in zip(np.diff(position), velocity[1:]):
        current_start, slow_cut = split_distance_forward(current_start, dx, min_segment_length_mm)
        if first:
            first = False
            line = current_start
        if not slow_cut:
            break

        def set_speed(line, set_velocity):
            if line.is_move:
                line.params['F'] = set_velocity * 60
        apply_forward(current_start, slow_cut, set_speed, set_velocity)

        current_start = next_continuous_move('moving_extrude', slow_cut)
        if current_start is None:
            break

        if set_velocity >= current_start.annotation.desired_feed_mms:
            break

    # Now that acceleration has finished, set the feed rate to the desired feed rate.
    if slow_cut:
        next_move = next_continuous_move('moving_extrude', slow_cut)
        if next_move:
            next_move.params['F'] = next_move.annotation.desired_feed_mms * 60

    return line

def apply(gcode: GCodeFile, options):
    # min_segment_length_mm = options['min_segment_length_mm']

    min_segment_length = 0.001

    square_corner_velocity_mms = 10

    dt_s = 0.010
    accel_dy_mmss = 10.0
    ramp_time_s = 0.200
    max_accel_mmss = 3000
    junction_threshold_mms = 1.0

    junction_deviation = (square_corner_velocity_mms**2) * (math.sqrt(2) - 1) / max_accel_mmss

    profile = SCurveAcceleration(ramp_time_s, max_accel_mmss, dt_s, accel_dy_mmss)

    section = gcode.first_section
    while section:
        if section.section_type not in ('outer wall', 'inner wall'):
        # if section.section_type not in ('outer wall',):
            section = section.next
            continue

        line = section.first_line
        while True:
            if line.annotation.move_type is None or line.annotation.desired_feed_mms is None or line.annotation.cos_theta is None or math.isnan(line.annotation.cos_theta):
                if line is section.last_line:
                    break
                line = line.next
                continue

            desired_feed_mms = line.annotation.desired_feed_mms
            junction_speed_mms = calc_junction_speed(max_accel_mmss, junction_deviation, line.annotation.cos_theta, desired_feed_mms)
            if abs(desired_feed_mms - junction_speed_mms) < junction_threshold_mms:
                if line is section.last_line:
                    break
                line = line.next
                continue

            accelerate_backward(line, junction_speed_mms, min_segment_length, profile)
            line = accelerate_forward(line, junction_speed_mms, min_segment_length, profile)

            if line is section.last_line:
                break
            line = line.next

        section = section.next


