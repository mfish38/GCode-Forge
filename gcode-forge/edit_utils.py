
from copy import deepcopy
from .parser import Section, Line
from .annotator import annotate

def next_move(move_type, line, stop=None):
    while True:
        line = line.next
        if line is None:
            break

        if line.annotation.move_type == move_type:
            return line

        if line is stop:
            break

    return None

def prev_continuous_move(move_type, line):
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
    # Travel back
    current = line
    traveled = 0
    while traveled < distance:
        current = current.prev

        if current.annotation.move_type in {
            'extrude',
            'retract',
            'z',
            'travel',
            'moving_retract',
        }:
            next_extrude = next_move('moving_extrude', current, stop=line)
            if next_extrude is line:
                return None
            return next_extrude

        traveled += current.annotation.distance_mm or 0
        # current.comment = (current.comment or '') + ' traveled: ' + str(traveled)

    # current is now the line to cut because it caused the distance to be exceeded
    current_length = current.annotation.distance_mm
    a_length = traveled - distance
    b_length = current_length - a_length

    # current.comment = (current.comment or '') + f' length: {current_length} a: {a_length}, b: {b_length}'

    # prevent undesirably small segments
    if a_length < min_segment_length or b_length < min_segment_length:
        if a_length < b_length:
            return current
        else:
            next_extrude = next_move('moving_extrude', current, stop=line)
            if next_extrude is line:
                return current
            return next_extrude

    a = Line(str(current))
    a.annotation._state = current.annotation._state

    b = Line(str(current))

    a_factor = a_length / current_length
    b_factor = b_length / current_length

    a_x, a_y = (current.annotation.vector * a_factor) + current.annotation.start_pos
    a.params['X'] = f'{a_x:.3f}'
    a.params['Y'] = f'{a_y:.3f}'

    if current_e := current.params.get('E'):
        current_e = float(current_e)
        a.params['E'] = f'{current_e * a_factor:.5f}'
        b.params['E'] = f'{current_e * b_factor:.5f}'

    current_section = current.section
    current_section.insert_after(current, a)
    current_section.insert_after(a, b)
    current_section.remove(current)

    annotate(a, line)

    return b
