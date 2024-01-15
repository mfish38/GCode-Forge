
from ..parser import GCodeFile, Line
from ..edit_utils import split_distance_back, prev_continuous_move

'''
This is a work in progress and has bugs.

TODO:
check split_distance function as distance does not seem correct
need to split_distance forward and restore feedrate
'''

def apply(gcode: GCodeFile, options):
    sharp_angle = options['sharp_angle']
    cut_distance = options['cut_distance']
    min_segment_length = 0.1

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

            slow = split_distance_back(line, cut_distance, min_segment_length)
            if slow:
                slow.section.insert_before(slow.prev, Line('; SLOW CUT'))
                while slow is not line:
                    if slow.code in ('G1', 'G0'):
                        slow.params['F'] = 10 * 60
                    slow = slow.next

            if line is section.last_line:
                break
            line = line.next

        section = section.next

