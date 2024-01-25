
from math import sqrt

from .parser import Line

# Assumes relative extrusion

# TODO: vectorize? Will need to track line number associations and re-associate

# Annotate linked list of continuous positive extrusion?

# @profile
def annotate(first: Line, last: Line=None, reannotate=False):
    '''
    Processes gcode lines and adds information about them to Line.annotation.
    '''
    # filament_diameter = 1.75

    if annotator_state := first.annotation._state:
        # If the first line already has a state then use that.
        previous_pos, current_pos, ba_norm, desired_feed = annotator_state
    else:
        # Initialize state tracked between lines.
        previous_pos = (float('NaN'), float('NaN'))
        current_pos = (float('NaN'), float('NaN'))
        ba_norm = float('NaN')
        desired_feed = None

    line = first
    while True:
        annotation = line.annotation

        # Store annotator state at the start of annotating the line so that we can restart at this
        # line and re-annotate it later.
        annotation._state = (
            previous_pos,
            current_pos,
            ba_norm,
            desired_feed
        )

        if line.is_move:
            # Annotate the desired feed rate
            if reannotate:
                # If we are re-annotating, then ignore feed rate parameters so that the desired feed
                # rate reflects the original gcode request rather than any modifications.
                if annotation.desired_feed_mms is not None:
                    desired_feed = annotation.desired_feed_mms
            elif (feed := line.params.get('F')) is not None:
                desired_feed = feed / 60

            annotation.desired_feed_mms = desired_feed

            # Annotate information about the angle of the move with relation to the previous move.
            # This will be done using vectors where `a` is the previous move start, `b` is this
            # move's start, and `c` is this moves end. The angle will be calculated as the angle
            # between b->a and b->c: a<-b->c.

            new_pos = (
                line.params.get('X', current_pos[0]),
                line.params.get('Y', current_pos[1]),
            )

            # b->a vector = a - b
            ba = (
                previous_pos[0] - current_pos[0],
                previous_pos[1] - current_pos[1]
            )

            # b->c vector = c - b
            bc = (
                new_pos[0] - current_pos[0],
                new_pos[1] - current_pos[1]
            )

            # Get the magnitude of the b->c vector.
            bc_norm = sqrt(bc[0]**2 + bc[1]**2)

            if bc_norm:
                annotation.start_pos = current_pos
                annotation.end_pos = new_pos
                annotation.distance_mm = bc_norm
                annotation.vector = bc

                ba_bc_norm = ba_norm * bc_norm

                if ba_bc_norm != 0:
                    # cos(theta) = (b->a dot b->c) / (||b->a|| * ||b->c||)
                    cos_theta = min(
                        max(
                            (ba[0] * bc[0] + ba[1] * bc[1]) / ba_bc_norm,
                            -1
                        ),
                        1
                    )
                    annotation.cos_theta = cos_theta

                    # TODO: have function in edit_utils to get angle as follows:
                    # angle_rads = math.acos(cos_theta)
                    # angle_deg = angle_rads * 180 / math.pi

                previous_pos = current_pos
                current_pos = new_pos
                ba_norm = bc_norm


            # Use the requested extrusion distance and the distance of the move to classify the type
            # of move.

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

        if last and line is last:
            break

        line = line.next
        if not line:
            break
