
import scipy as sc

from ..parser import GCodeFile, Line

def apply(gcode: GCodeFile, options):
    pa_lut = sc.interpolate.make_interp_spline(options['speeds'], options['pa_values'], bc_type="natural")

    min_speed = options['speeds'][0]
    max_speed = options['speeds'][-1]

    for section in gcode.sections:
        new_lines = []
        for line in section.lines:
            if line.code in ('G1', 'G0') and 'F' in line.params:
                feed_mms = float(line.params['F']) / 60

                new_pa = pa_lut(
                    min(
                        max(feed_mms, min_speed),
                        max_speed
                    )
                )

                new_lines.append(Line(f'SET_PRESSURE_ADVANCE ADVANCE={new_pa:.3f}'))

            new_lines.append(line)

        section.lines = new_lines
