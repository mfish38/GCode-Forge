
import math

import numpy as np

from .parser import Line

np.seterr('raise')

# Assumes relative extrusion

# TODO: vectorize. Will need to track line number associations and re-associate

# Annotate linked list of continuous positive extrusion?

def annotate(first: Line, last: Line=None, reannotate=False):
    filament_diameter = 1.75

    if annotator_state := first.annotation._state:
        previous_pos, current_pos, ba_norm, desired_feed = annotator_state
    else:
        previous_pos = np.array([float('NaN'), float('NaN')])
        current_pos = np.array([float('NaN'), float('NaN')])
        ba_norm = float('NaN')
        desired_feed = None

    line = first
    while True:
        annotation = line.annotation

        # Store annotator state at the start of annotating the line so that we can restart at this line and re-annotate it.
        annotation._state = [
            previous_pos,
            current_pos,
            ba_norm,
            desired_feed
        ]

        if line.code in ('G1', 'G0'):
            if reannotate:
                if annotation.desired_feed_mms is not None:
                    desired_feed = annotation.desired_feed_mms
            elif (feed := line.params.get('F')) is not None:
                desired_feed = feed

            annotation.desired_feed_mms = desired_feed

            new_pos = np.array([
                line.params.get('X', current_pos[0]),
                line.params.get('Y', current_pos[1]),
            ])

            # a<-b->c
            ba = previous_pos - current_pos
            bc = new_pos - current_pos

            # Faster than bc_norm = np.linalg.norm(bc)
            bc_norm = math.sqrt(bc.dot(bc))

            if bc_norm:
                annotation.start_pos = current_pos
                annotation.end_pos = new_pos
                annotation.distance_mm = bc_norm
                annotation.vector = bc

                ba_bc_norm = ba_norm * bc_norm

                if ba_bc_norm == 0:
                    angle_deg = None
                else:
                    angle_rads = math.acos(
                        min(
                            max(
                                np.dot(ba, bc) / ba_bc_norm,
                                -1
                            ),
                            1
                        )
                    )
                    angle_deg = angle_rads * 180 / math.pi
                annotation.angle_deg = angle_deg

                previous_pos = current_pos
                current_pos = new_pos
                ba_norm = bc_norm


            extrude_distance = line.params.get('E', 0)

            # extrude_mm3 = extrude_distance * math.pi * (filament_diameter ** 2)
            # annotation.extrude_mm3 = extrude_mm3

            if bc_norm < 0.0001:
                if extrude_distance > 0.000001:
                    move_type = 'extrude'
                elif extrude_distance < -0.000001:
                    move_type = 'retract'
                elif 'Z' in line.params:
                    # TODO: track current z and set only if z changes?
                    move_type = 'z'
                elif 'F' in line.params:
                    move_type = 'set_feed'
                else:
                    move_type = 'noop'
            else:
                if extrude_distance > 0.000001:
                    move_type = 'moving_extrude'
                elif extrude_distance < -0.000001:
                    move_type = 'moving_retract'
                else:
                    move_type = 'travel'

            annotation.move_type = move_type

            # line.comment = move_type
            # line.comment = f'{angle_deg:.1f} {bc_norm:.1f}'

        if last and line is last:
            break

        line = line.next
        if not line:
            break