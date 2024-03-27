
import math

from ..parser import GCodeFile, Line
from ..edit_utils import split_distance_back, split_distance_forward, next_continuous_move, apply_forward, apply_backward

# This is another experiment based on accel_experiment with some cleanup

def accelerate_backward(line: Line, from_mms: float, step_distance_mm: float, min_segment_length_mm: float, accel_exponent: float, accel_scale_x: float, accel_scale_y: float):
    current_start = line
    feed_rate_mms = from_mms
    traveled = 0
    while True:
        slow_cut = split_distance_back(current_start, step_distance_mm, min_segment_length_mm)

        if not slow_cut:
            break

        def set_speed(line):
            if line.is_move:
                if 'F' in line.params:
                    current_line_feed_mms = line.params['F'] / 60
                    if current_line_feed_mms <= feed_rate_mms:
                        return True

                line.params['F'] = feed_rate_mms * 60
        stop = apply_backward(current_start, slow_cut, set_speed)

        if stop:
            break

        current_start = slow_cut

        traveled += step_distance_mm

        feed_rate_mms = from_mms + ((traveled * accel_scale_x) ** accel_exponent * accel_scale_y)
        if feed_rate_mms >= current_start.annotation.desired_feed_mms:
            break

def accelerate_forward(line: Line, from_mms: float, step_distance_mm: float, min_segment_length_mm: float, accel_exponent: float, accel_scale_x: float, accel_scale_y: float):
    first = True
    current_start = line
    feed_rate_mms = from_mms
    traveled = 0
    while True:
        current_start, slow_cut = split_distance_forward(current_start, step_distance_mm, min_segment_length_mm)
        if first:
            first = False
            line = current_start

        if not slow_cut:
            break

        def set_speed(line):
            if line.is_move:
                line.params['F'] = feed_rate_mms * 60
        apply_forward(current_start, slow_cut, set_speed)

        current_start = next_continuous_move('moving_extrude', slow_cut)
        if current_start is None:
            break

        traveled += step_distance_mm

        feed_rate_mms = from_mms + ((traveled * accel_scale_x) ** accel_exponent * accel_scale_y)
        if feed_rate_mms >= current_start.annotation.desired_feed_mms:
            break

    # Now that acceleration has finished, set the feed rate to the desired feed rate.
    if slow_cut:
        slow_cut.section.insert_after(slow_cut, Line(f'G1 F{slow_cut.annotation.desired_feed_mms * 60} ; restore'))

    return line

def apply(gcode: GCodeFile, options):
    additional_slow_distance_mm = options['additional_slow_distance_mm']
    slow_speed_mms = options['slow_speed_mms']
    accel_step_distance_mm = options['accel_step_distance_mm']
    threshold_angle = options['threshold_angle']
    min_segment_length_mm = options['min_segment_length_mm']

    accel_exponent = options['accel_exponent']
    accel_scale_y = options['accel_scale_y']
    accel_scale_x = options['accel_scale_x']

    section = gcode.first_section
    while section:
        if section.section_type not in ('outer wall', 'inner wall'):
            section = section.next
            continue

        line = section.first_line
        while True:
            if line.annotation.move_type is None or line.annotation.desired_feed_mms is None or line.annotation.cos_theta is None or math.isnan(line.annotation.cos_theta):
                if line is section.last_line:
                    break
                line = line.next
                continue

            angle_rads = math.acos(line.annotation.cos_theta)
            angle_deg = angle_rads * 180 / math.pi

            if angle_deg > threshold_angle:
                if line is section.last_line:
                    break
                line = line.next
                continue

            slow_cut = split_distance_back(line, additional_slow_distance_mm, min_segment_length_mm)
            if slow_cut:
                def set_speed_back(line):
                    if line.is_move:
                        if 'F' in line.params:
                            current_line_feed_mms = line.params['F'] / 60
                            if current_line_feed_mms <= slow_speed_mms:
                                return True

                        line.params['F'] = slow_speed_mms * 60
                stop = apply_backward(line, slow_cut, set_speed_back)

                if not stop:
                    accelerate_backward(slow_cut, slow_speed_mms, accel_step_distance_mm, min_segment_length_mm, accel_exponent, accel_scale_x, accel_scale_y)

            line, slow_cut = split_distance_forward(line, additional_slow_distance_mm, min_segment_length_mm)
            if slow_cut:
                def set_speed_forward(line):
                    if line.is_move:
                        line.params['F'] = slow_speed_mms * 60
                apply_forward(line, slow_cut, set_speed_forward)
                slow_cut.section.insert_after(slow_cut, Line(f'G1 F{slow_cut.annotation.desired_feed_mms * 60} ; restore'))

                slow_cut = accelerate_forward(slow_cut.next, slow_speed_mms, accel_step_distance_mm, min_segment_length_mm, accel_exponent, accel_scale_x, accel_scale_y)

            if line is section.last_line:
                break
            line = line.next

        section = section.next


