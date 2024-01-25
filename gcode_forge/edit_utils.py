
from .parser import Line
from .annotator import annotate

def next_move(line, stop=None):
    '''
    Gets the first next move after the given line.
    '''
    while True:
        line = line.next
        if line is None:
            break

        if line.annotation.move_type is not None:
            return line

        if line is stop:
            break

    return None

def prev_move(line, stop=None):
    '''
    Gets the first previous move after the given line.
    '''
    while True:
        line = line.prev
        if line is None:
            break

        if line.annotation.move_type is not None:
            return line

        if line is stop:
            break

    return None

def prev_continuous_move(move_type, line):
    '''
    Gets the first previous move of the given move type in a sequence of continuous forward
    extrusion that the given line belongs to.
    '''
    while True:
        line = line.prev
        if line is None:
            break

        if line.annotation.move_type in {
            'extrude',
            'retract',
            'z',
            'travel',
            'moving_retract',
        }:
            break

        if line.annotation.move_type == move_type:
            return line

    return None

def next_continuous_move(move_type, line):
    '''
    Gets the first next move of the given move type in a sequence of continuous forward
    extrusion that the given line belongs to.
    '''
    while True:
        line = line.next
        if line is None:
            break

        if line.annotation.move_type in {
            'extrude',
            'retract',
            'z',
            'travel',
            'moving_retract',
        }:
            break

        if line.annotation.move_type == move_type:
            return line

    return None

def split_distance_back(line: Line, distance:float, min_segment_length:float):
    '''
    Splits a previous line segment at a given distance back from the start of the given line.

    If the split would result in the segment to either side of the cut being less than
    min_segment_length, the closest existing split to where the cut would have occurred is used
    instead.

    Stops early if a break in the extrusion line is encountered. Returns None if such a line directly
    precedes the line.

    Returns the line closest to the cut between the given line and the cut.
    '''
    # Travel back until we have exceeded the given distance
    current = line
    traveled = 0
    while traveled < distance:
        current = current.prev

        if current is None:
            return current

        traveled += current.annotation.distance_mm or 0

    # `current` is now the line to cut because it caused the distance to be exceeded. Determine the
    # length of two new line segments where the line segments are as follows:
    #   a -> b -> start
    current_length = current.annotation.distance_mm
    a_length = traveled - distance
    b_length = current_length - a_length

    # Prevent undesirably small segments
    if a_length < min_segment_length or b_length < min_segment_length:
        if a_length < b_length:
            return current
        else:
            next_extrude = next_move(current, stop=line)
            if next_extrude is line:
                return current
            return next_extrude

    # Create the two new line segments to replace the existing line.
    a = current.copy()
    a.annotation._state = current.annotation._state

    b = current.copy()

    # Determine the scaling of the new lines to the existing line.
    a_factor = a_length / current_length
    b_factor = b_length / current_length

    # Only `a` needs new x and y parameters as `b` will have the same end point as the existing line.
    # vector * a_factor + start_pos
    vector = current.annotation.vector
    start_pos = current.annotation.start_pos
    a.params['X'] = vector[0] * a_factor + start_pos[0]
    a.params['Y'] = vector[1] * a_factor + start_pos[1]

    # Scale the extrusion amounts by the scale of the new lines to the existing line.
    if current_e := current.params.get('E'):
        a.params['E'] = current_e * a_factor
        b.params['E'] = current_e * b_factor

    # Replace the existing line segment.
    current_section = current.section
    current_section.insert_after(current, a)
    current_section.insert_after(a, b)
    current_section.remove(current)

    # Reannotate so that the annotations are correct.
    annotate(a, line, reannotate=True)

    return b

def split_distance_forward(line: Line, distance:float, min_segment_length:float):
    '''
    Like split_distance_back but in the other direction.

    Note that the line itself may be split as its start is the starting point

    Returns the last line before the cut. Also returns the starting line that was passed in case it
    was cut as outside references to it are now invalid.
    '''
    # Travel forward until we have exceeded the given distance.
    current = line
    traveled = current.annotation.distance_mm or 0
    while traveled < distance:
        current = current.next

        if current is None:
            return line, current

        traveled += current.annotation.distance_mm or 0

    # `current` is now the line to cut because it caused the distance to be exceeded. Determine the
    # length of two new line segments where the line segments are as follows:
    #   start -> a -> b
    current_length = current.annotation.distance_mm
    b_length = traveled - distance
    a_length = current_length - b_length

    # Prevent undesirably small segments
    if a_length < min_segment_length or b_length < min_segment_length:
        if a_length < b_length:
            prev_extrude = prev_move(current, stop=line)
            return line, prev_extrude
        else:
            return line, current

    # Create the two new line segments to replace the existing line.
    a = current.copy()
    a.annotation._state = current.annotation._state

    b = current.copy()

    # Determine the scaling of the new lines to the existing line.
    a_factor = a_length / current_length
    b_factor = b_length / current_length

    # Only `a` needs new x and y parameters as `b` will have the same end point as the existing line.
    # vector * a_factor + start_pos
    vector = current.annotation.vector
    start_pos = current.annotation.start_pos
    a.params['X'] = vector[0] * a_factor + start_pos[0]
    a.params['Y'] = vector[1] * a_factor + start_pos[1]

    # Scale the extrusion amounts by the scale of the new lines to the existing line.
    if current_e := current.params.get('E'):
        a.params['E'] = current_e * a_factor
        b.params['E'] = current_e * b_factor

    # Replace the existing line segment.
    current_section = current.section
    current_section.insert_after(current, a)
    current_section.insert_after(a, b)
    current_section.remove(current)

    # If the line that was replaced was the line given as the starting point, we need to return `a`
    # as what the caller should use going forward instead of the given line.
    if current is line:
        line = a

    # Reannotate so that the annotations are correct.
    annotate(a, b, reannotate=True)

    return line, a
