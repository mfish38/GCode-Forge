
import math
from dataclasses import dataclass

import numpy as np

from .parser import Line

np.seterr('raise')

# Assumes relative extrusion

# TODO: vectorize. Will need to track line number associations and re-associate

def annotate(first: Line, last: Line=None):
    filament_diameter = 1.75

    if annotator_state := first.metadata.get('annotator_state'):
        previous_pos, current_pos, ba_norm = annotator_state
    else:
        previous_pos = np.array([float('NaN'), float('NaN')])
        current_pos = np.array([float('NaN'), float('NaN')])
        ba_norm = float('NaN')

    line = first
    while True:
        # Store annotator state at the start of annotating the line so that we can restart at this line and re-annotate it.
        line.metadata['annotator_state'] = [
            previous_pos,
            current_pos,
            ba_norm
        ]

        if line.code in ('G1', 'G0'):
            new_pos = np.array([
                float(line.params.get('X', current_pos[0])),
                float(line.params.get('Y', current_pos[1])),
            ])

            # a<-b->c
            ba = previous_pos - current_pos
            bc = new_pos - current_pos

            bc_norm = np.linalg.norm(bc)
            if bc_norm:
                line.metadata['start_pos'] = current_pos
                line.metadata['end_pos'] = new_pos
                line.metadata['distance_mm'] = bc_norm
                line.metadata['vector'] = bc

                ba_bc_norm = ba_norm * bc_norm

                if ba_bc_norm == 0:
                    angle_deg = None
                else:
                    angle_rads = math.acos(
                        np.clip(
                            np.dot(ba, bc)
                            / ba_bc_norm,
                            -1,
                            1
                        )
                    )
                    angle_deg = angle_rads * 180 / math.pi
                line.metadata['angle_deg'] = angle_deg

                previous_pos = current_pos
                current_pos = new_pos
                ba_norm = bc_norm


            extrude_distance = float(line.params.get('E', 0))

            extrude_mm3 = extrude_distance * math.pi * (filament_diameter ** 2)

            line.metadata['extrude_mm3'] = extrude_mm3

        if last and line is last:
            break

        line = line.next
        if not line:
            break
