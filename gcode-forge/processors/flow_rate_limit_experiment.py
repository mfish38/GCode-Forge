
import numpy as np

from ..parser import GCodeFile, Line
from ..edit_utils import split_distance_back, prev_continuous_move

def apply(gcode: GCodeFile, options):
    sharp_angle = options['sharp_angle_deg']
    step_distance = options['step_distance']
    angle_speed = options['angle_speed_mms'] * 60
    steps = options['steps'] + 1
    min_segment_length = 0.012

    current_feed_rate = None

    section = gcode.first_section
    while section:
        line = section.first_line
        while True:
            current_feed_rate = line.params.get('F', current_feed_rate)

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

            line.params['F'] = current_feed_rate

            feed_rates = np.linspace(angle_speed, float(current_feed_rate), steps)[:-1]
            current_start = line
            for feed_rate in feed_rates:
                slow_cut = split_distance_back(current_start, step_distance, min_segment_length)

                if not slow_cut:
                    break

                # slow_cut.section.insert_before(slow_cut, Line('; SLOW CUT'))
                stop = False
                current_line = current_start.prev
                while True:
                    if current_line.code in ('G1', 'G0'):
                        if 'F' in current_line.params:
                            current_line_feed = float(current_line.params['F'])
                            if current_line_feed <= feed_rate:
                                stop = True
                                break

                        current_line.params['F'] = f'{feed_rate:.1f}'

                    if current_line is slow_cut:
                        break

                    current_line = current_line.prev

                if stop:
                    break

                current_start = slow_cut

            if line is section.last_line:
                break
            line = line.next

        section = section.next

