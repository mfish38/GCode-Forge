from time import time
from pathlib import Path
from importlib import import_module

from . import parser
from . import annotator

def main(args):
    start = time()

    # Load and process the gcode file.
    path = Path(args[1])
    text = path.read_text()
    gcode = parser.parse(text)
    annotator.annotate(gcode.first_section.first_line)

    SHELL_PA = 0.37
    INFILL_PA = 0.0

    # Configuration defining what gcode processors will run and with what settings.
    processors = {
        'line_type_pa': {
            'default_pa': SHELL_PA,
            'pa_values': {
                'internal solid infill': INFILL_PA,
                'top surface': SHELL_PA,
                'gap infill': INFILL_PA,
                'sparse infill': INFILL_PA,
                'internal bridge': INFILL_PA,
                'outer wall': SHELL_PA,
                'overhang wall': SHELL_PA,
                'bridge': SHELL_PA,
                'inner wall': SHELL_PA,
                'bottom surface': SHELL_PA
            }
        },

        # Note: speed based LUT is experimental. Also does not account for line width and acceleration.
        # TODO: rewrite speed_lut_pa to use new linked list file representation
        # 'speed_lut_pa': {
        #     'speeds': [100, 150, 200, 250, 300],
        #     'pa_values': [0.62, 0.48, 0.36, 0.292, 0.28]
        # }

        # Experimental, incomplete hand has bugs
        # 'accel_experiment': {
        #     'step_distance_mm': 0.25,
        #     'acceleration_mmss': 8000.0,
        #     'square_corner_velocity_mms': 5.0
        # }
    }


    # Run the processors.
    for processor_name, options in processors.items():
        module = import_module('.processors.' + processor_name, package='gcode_forge')
        module.apply(gcode, options)


    # Write the output.
    output = str(gcode)
    path.write_text(output, newline='\n', encoding='UTF-8')
    # Path('out.gcode').write_text(output, newline='\n', encoding='UTF-8')

    print(time() - start)

if __name__ == '__main__':
    import sys
    main(sys.argv)