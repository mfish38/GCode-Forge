
from ..parser import GCodeFile, Line
from ..edit_utils import split_distance_back

'''
This is a work in progress and has bugs.

TODO: ignore sharp angle caused by start after travel move
check split_distance function as distance does not seem correct
need to split_distance forward and restore feedrate
does not appear to cut backwards when it should in some instances
'''

def apply(gcode: GCodeFile, options):
    sharp_angle = options['sharp_angle']
    cut_distance = options['cut_distance']
    min_segment_length = 0.1

    section = gcode.first_section
    while section:
        line = section.first_line
        while True:
            if line.metadata.get('angle_deg', 180) < sharp_angle:
                section.insert_before(
                    line,
                    Line('; SHARP ANGLE')
                )

                slow = split_distance_back(line, cut_distance, min_segment_length)
                if slow:
                    slow.section.insert_before(slow.prev, Line('; SLOW CUT'))
                    while slow is not line.next:
                        if slow.code in ('G1', 'G0'):
                            slow.params['F'] = 10 * 60
                        slow = slow.next

            if line is section.last_line:
                break
            line = line.next

        section = section.next

