
from ..parser import GCodeFile, Line

def apply(gcode: GCodeFile, options):
    pa_values = options['pa_values']

    current_pa = options['default_pa']
    for section in gcode.sections:
        current_pa = pa_values.get(section.section_type, current_pa)

        new_lines = [
            Line(f'SET_PRESSURE_ADVANCE ADVANCE={current_pa:.3f}')
        ]

        new_lines.extend(section.lines)

        section.lines = new_lines
