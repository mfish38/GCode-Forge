
from ..parser import GCodeFile, Line

def apply(gcode: GCodeFile, options):
    sharp_angle = options['sharp_angle']

    for section in gcode.sections:
        new_lines = []

        for line in section.lines:
            if line.metadata.get('angle_deg', 180) < sharp_angle:
                new_lines.append(Line('; SHARP ANGLE'))

            new_lines.append(line)

        section.lines = new_lines

