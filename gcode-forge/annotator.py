
import math
from dataclasses import dataclass

import numpy as np

from .parser import GCodeFile

np.seterr('raise')

# Assumes relative extrusion

def annotate(gcode: GCodeFile):
    filament_diameter = 1.75
    previous_pos = np.array([float('NaN'), float('NaN')])
    current_pos = np.array([float('NaN'), float('NaN')])
    ba_norm = float('NaN')

    for section in gcode.sections:
        for line in section.lines:
            if line.code in ('G1', 'G0'):
                new_pos = np.array([
                    float(line.params.get('X', current_pos[0])),
                    float(line.params.get('Y', current_pos[1])),
                ])

                # a->b->c
                ba = previous_pos - current_pos
                bc = new_pos - current_pos

                bc_norm = np.linalg.norm(bc)
                if bc_norm:
                    line.metadata['distance'] = bc_norm

                    ba_bc_norm = ba_norm * bc_norm

                    if ba_bc_norm == 0:
                        angle = None
                    else:
                        angle = math.acos(
                            np.clip(
                                np.dot(ba, bc)
                                / ba_bc_norm,
                                -1,
                                1
                            )
                        )
                    line.metadata['angle'] = angle

                    previous_pos = current_pos
                    current_pos = new_pos
                    ba_norm = bc_norm


                extrude_distance = float(line.params.get('E', 0))

                extrude_mm3 = extrude_distance * math.pi * (filament_diameter ** 2)

                line.metadata['extrude_mm3'] = extrude_mm3

                line.comment = str(line.metadata)

