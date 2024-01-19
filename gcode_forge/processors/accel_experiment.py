
import math

from ..parser import GCodeFile, Line
from ..edit_utils import split_distance_back, prev_continuous_move, split_distance_forward, next_continuous_move

FEED_MMS_EPSILON = 0.001 * 60

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

def accelerate_backward(line: Line, from_mms: float, step_distance_mm: float, min_segment_length_mm: float, acceleration_mmss: float):
    '''
    Apply acceleration down to the junction velocity by splitting the proceeding lines
    into segments of increasing velocity until the desired feed rate leading into the
    junction is hit, or the feed rate is already lower (possibly set by acceleration from
    a previous junction).
    '''
    current_start = line
    feed_rate_mms = from_mms
    while True:
        slow_cut = split_distance_back(current_start, step_distance_mm, min_segment_length_mm)

        if not slow_cut:
            break

        # Apply to all segments between the start and the cut.
        stop = False
        current_line = current_start.prev
        while True:
            if current_line.code in ('G1', 'G0'):
                if 'F' in current_line.params:
                    current_line_feed_mms = current_line.params['F'] / 60
                    if current_line_feed_mms <= feed_rate_mms:
                        stop = True
                        break

                current_line.params['F'] = feed_rate_mms * 60

            if current_line is slow_cut:
                break

            current_line = current_line.prev

        if stop:
            break

        current_start = slow_cut

        feed_rate_mms = math.sqrt(feed_rate_mms**2 + 2 * acceleration_mmss * step_distance_mm)
        if feed_rate_mms >= current_start.annotation.desired_feed_mms:
            break

def accelerate_forward(line: Line, from_mms: float, step_distance_mm: float, min_segment_length_mm: float, acceleration_mmss: float):
    '''
    Apply acceleration up from the junction velocity by splitting the following lines
    into segments of increasing velocity until the desired feed rate leaving the
    junction is hit.
    '''
    first = True
    current_start = line
    feed_rate_mms = from_mms
    while True:
        current_start, slow_cut = split_distance_forward(current_start, step_distance_mm, min_segment_length_mm)
        if first:
            first = False
            line = current_start

        if not slow_cut:
            break

        current_line = current_start
        while True:
            if current_line.code in ('G1', 'G0'):
                current_line.params['F'] = feed_rate_mms * 60

            if current_line is slow_cut:
                break

            current_line = current_line.next

        current_start = next_continuous_move('moving_extrude', slow_cut)
        if current_start is None:
            break

        feed_rate_mms = math.sqrt(feed_rate_mms**2 + 2 * acceleration_mmss * step_distance_mm)
        if feed_rate_mms >= current_start.annotation.desired_feed_mms:
            break

    # Now that acceleration has finished, set the feed rate to the desired feed rate.
    if slow_cut:
        slow_cut.section.insert_after(slow_cut, Line(f'G1 F{slow_cut.annotation.desired_feed_mms * 60} ; restore'))

    return line


def apply(gcode: GCodeFile, options):
    step_distance_mm = options['step_distance_mm']
    acceleration_mmss = options['acceleration_mmss']
    square_corner_velocity_mms = options['square_corner_velocity_mms']

    junction_deviation = (square_corner_velocity_mms**2) * (math.sqrt(2) - 1) / acceleration_mmss

    # When cutting the moves to make velocity changes, if the cut falls within this distance of an
    # existing junction, that junction will be used instead of making a new one, preventing super
    # tiny line segments below this size.
    min_segment_length = 0.1

    section = gcode.first_section
    while section:
        line = section.first_line
        while True:
            if line.annotation.move_type != 'moving_extrude':
                if line is section.last_line:
                    break
                line = line.next
                continue

            # TODO: need to calculate junction speed and accel for travel moves as well.

            if not prev_continuous_move('moving_extrude', line):
                # line = accelerate_forward(line, 5, step_distance_mm, min_segment_length, acceleration_mmss)

                if line is section.last_line:
                    break
                line = line.next
                continue

            if not next_continuous_move('moving_extrude', line):
                # accelerate_backward(line.next, 5, step_distance_mm, min_segment_length, acceleration_mmss)

                if line is section.last_line:
                    break
                line = line.next
                continue

            desired_feed_mms = line.annotation.desired_feed_mms
            junction_speed_mms = calc_junction_speed(acceleration_mmss, junction_deviation, line.annotation.cos_theta, desired_feed_mms)
            if desired_feed_mms - junction_speed_mms < FEED_MMS_EPSILON:
                if line is section.last_line:
                    break
                line = line.next
                continue

            accelerate_backward(line, junction_speed_mms, step_distance_mm, min_segment_length, acceleration_mmss)
            accelerate_forward(line, junction_speed_mms, step_distance_mm, min_segment_length, acceleration_mmss)

            if line is section.last_line:
                break
            line = line.next

        section = section.next

