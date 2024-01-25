
import scipy as sc

from ..parser import GCodeFile, Line

def apply(gcode: GCodeFile, options):
    pa_lut = sc.interpolate.make_interp_spline(options['speeds'], options['pa_values'], bc_type="natural")

    min_speed = options['speeds'][0]
    max_speed = options['speeds'][-1]

    section = gcode.first_section
    while section:
        line = section.first_line
        while True:
            if line.is_move and 'F' in line.params:
                feed_mms = line.params['F'] / 60

                new_pa = pa_lut(
                    min(
                        max(feed_mms, min_speed),
                        max_speed
                    )
                )

                section.insert_before(
                    line,
                    Line(f'SET_PRESSURE_ADVANCE ADVANCE={new_pa:.3f}')
                )

            if line is section.last_line:
                break
            line = line.next

        section = section.next
