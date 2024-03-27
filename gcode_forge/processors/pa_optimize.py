
import math

from ..parser import GCodeFile, Line
from ..edit_utils import split_distance_back, prev_continuous_move, split_distance_forward, next_continuous_move, apply_forward, apply_backward

# This is another experiment based on accel_experiment with some cleanup

def apply(gcode: GCodeFile, options):
    slow_distance_mm = 1.0
    slow_speed_mms = 40
    threshold_angle = 140
    min_segment_length_mm = 0.1

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

            slow_cut = split_distance_back(line, slow_distance_mm, min_segment_length_mm)
            if slow_cut:
                def set_speed_back(line):
                    if line.is_move:
                        if 'F' in line.params:
                            current_line_feed_mms = line.params['F'] / 60
                            if current_line_feed_mms <= slow_speed_mms:
                                return True

                        line.params['F'] = slow_speed_mms * 60
                apply_backward(line, slow_cut, set_speed_back)

            line, slow_cut = split_distance_forward(line, slow_distance_mm, min_segment_length_mm)
            if slow_cut:
                def set_speed_forward(line):
                    if line.is_move:
                        line.params['F'] = slow_speed_mms * 60
                apply_forward(line, slow_cut, set_speed_forward)

                slow_cut.section.insert_after(slow_cut, Line(f'G1 F{slow_cut.annotation.desired_feed_mms * 60} ; restore'))

            if line is section.last_line:
                break
            line = line.next

        section = section.next


