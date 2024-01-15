
from ..parser import GCodeFile, Line

def apply(gcode: GCodeFile, options):
    pa_values = options['pa_values']

    current_pa = options['default_pa']

    section = gcode.first_section
    while section:
        current_pa = pa_values.get(section.section_type, current_pa)

        section.insert_before(
            section.first_line,
            Line(f'SET_PRESSURE_ADVANCE ADVANCE={current_pa:.3f}')
        )

        section = section.next
