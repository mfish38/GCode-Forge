import sys
from pathlib import Path
from importlib import import_module

from . import parser

path = Path(sys.argv[1])

text = path.read_text()
gcode = parser.parse(text)

SHELL_PA = 0.62
INFILL_PA = 0.28

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
    }
}

for processor_name, options in processors.items():
    module = import_module('.processors.' + processor_name, package='gcode-forge')
    module.apply(gcode, options)

output = str(gcode)

# print(output)
path.write_text(output, newline='\n', encoding='UTF-8')