
from ..parser import GCodeFile, Line

def apply(gcode: GCodeFile, options):
    sharp_angle = options['sharp_angle']

    section = gcode.first_section
    while section:
        line = section.first_line
        while True:
            if line.metadata.get('angle_deg', 180) < sharp_angle:
                section.insert_before(
                    line,
                    Line('; SHARP ANGLE')
                )

            if line is section.last_line:
                break
            line = line.next

        section = section.next

