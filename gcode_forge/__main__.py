from time import time
from pathlib import Path
from importlib import import_module

import yaml
import jinja2

from . import parser
from . import annotator

def expand_config_section(macros, config_section):
    jinja_env = jinja2.Environment(
        loader=jinja2.DictLoader({
            'macros': macros,
            'config': '{% import \'macros\' as macros %}' + config_section
        })
    )

    return jinja_env.get_template('config').render()

def structure_map(structure, function):
    if isinstance(structure, dict):
        return {k: structure_map(v, function) for k, v in structure.items()}
    elif isinstance(structure, list):
        return [structure_map(x, function) for x in structure]
    elif isinstance(structure, tuple):
        return tuple(structure_map(x, function) for x in structure)

    return function(structure)

def main(args):
    start = time()

    # Load the config
    config_path = Path(args[1])
    config = yaml.safe_load(config_path.read_text())
    macros = config['macros']

    processors = config['processors']
    processors = structure_map(processors, lambda x: expand_config_section(macros, x) if isinstance(x, str) else x)

    # Load and process the gcode file.
    path = Path(args[2])
    text = path.read_text()
    gcode = parser.parse(text)
    annotator.annotate(gcode.first_section.first_line)

    # Configuration defining what gcode processors will run and with what settings.
    # processors={
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
    # }

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