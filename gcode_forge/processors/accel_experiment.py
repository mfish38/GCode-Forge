
import math
import numpy as np

from ..parser import GCodeFile, Line
from ..edit_utils import split_distance_back, prev_continuous_move, split_distance_forward

# TODO: rewrite to calculate junction speed instead of a single angle speed for sharp angles?
# although current approach only does accel on sharp angles, which may be the prefered approach for print speed
# def junction_speed(max_accel_mmss, deviation):
#     # https://onehossshay.wordpress.com/2011/09/24/improving_grbl_cornering_algorithm/
#     already have cos_theta from angle calc in annotator
#     sin_half_theta = math.sqrt((1 - cos_theta) / 2)
#     r = deviation * (sin_half_theta / (1 - sin_half_theta))
#     return math.sqrt(max_accel_mmss * r)

# TODO: acceleration from continuous extrusion start and decel to stop

def apply(gcode: GCodeFile, options):
    sharp_angle = options['sharp_angle_deg']
    step_distance_mm = options['step_distance_mm']
    angle_speed_mms = options['angle_speed_mms']
    acceleration_mmss = options['acceleration_mmss']

    # When cutting the moves to make velocity changes, if the cut falls within this distance of an
    # existing junction, that junction will be used instead of making a new one, preventing super
    # tiny line segments below this size.
    min_segment_length = 0.1

    section = gcode.first_section
    while section:
        line = section.first_line
        while True:
            if line.annotation.angle_deg is None:
                if line is section.last_line:
                    break
                line = line.next
                continue

            if line.annotation.angle_deg > sharp_angle:
                if line is section.last_line:
                    break
                line = line.next
                continue

            if not (
                line.annotation.move_type == 'moving_extrude'
                and prev_continuous_move('moving_extrude', line)
            ):
                if line is section.last_line:
                    break
                line = line.next
                continue

            section.insert_before(
                line,
                Line('; SHARP ANGLE')
            )

            # TODO: implement actual acceleration rather than linear velocity ramp steps
            # Apply acceleration down to the junction velocity by splitting the proceeding lines
            # into segments of increasing velocity until the desired feed rate leading into the
            # junction is hit, or the feed rate is already lower (possibly set by acceleration from
            # a previous junction).
            current_start = line
            feed_rate = angle_speed_mms
            while True:
                slow_cut = split_distance_back(current_start, step_distance_mm, min_segment_length)

                if not slow_cut:
                    break

                # Apply to all segments between the start and the cut.
                stop = False
                current_line = current_start.prev
                while True:
                    if current_line.code in ('G1', 'G0'):
                        if 'F' in current_line.params:
                            current_line_feed = current_line.params['F'] / 60
                            if current_line_feed <= feed_rate:
                                stop = True
                                break

                        current_line.params['F'] = feed_rate * 60

                    if current_line is slow_cut:
                        break

                    current_line = current_line.prev

                if stop:
                    break

                current_start = slow_cut

                feed_rate = math.sqrt(feed_rate**2 + 2 * acceleration_mmss * step_distance_mm)
                if feed_rate >= line.annotation.desired_feed_mms / 60:
                    break

            # TODO: implement actual acceleration rather than linear velocity ramp steps
            # Apply acceleration up from the junction velocity by splitting the following lines
            # into segments of increasing velocity until the desired feed rate leaving the
            # junction is hit.
            first = True
            current_start = line
            feed_rate = angle_speed_mms
            while True:
                current_start, slow_cut = split_distance_forward(current_start, step_distance_mm, min_segment_length)
                if first:
                    first = False
                    line = current_start

                if not slow_cut:
                    break

                current_line = current_start
                while True:
                    if current_line.code in ('G1', 'G0'):
                        current_line.params['F'] = feed_rate * 60

                    if current_line is slow_cut:
                        break

                    current_line = current_line.next

                current_start = slow_cut.next

                feed_rate = math.sqrt(feed_rate**2 + 2 * acceleration_mmss * step_distance_mm)
                if feed_rate >= line.annotation.desired_feed_mms / 60:
                    break

            # Now that acceleration has finished, set the feed rate to the desired feed rate.
            if slow_cut:
                section.insert_after(slow_cut, Line(f'G1 F{slow_cut.annotation.desired_feed_mms}'))

            if line is section.last_line:
                break
            line = line.next

        section = section.next

