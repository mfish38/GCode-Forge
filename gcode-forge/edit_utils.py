
from copy import deepcopy
from .parser import Section, Line
from .annotator import annotate

def split_distance_back(line: Line, distance:float, min_segment_length:float):
    '''
    Splits a previous line segment at a given distance back from the start of the given line.

    If the split would result in the segment to either side of the cut being less than
    min_segment_length, the closest existing split to where the cut would have occurred is used
    instead.

    Stops and returns early if there is a Z parameter, a negative E parameter, or no E parameter when there is a distance traveled.
    Returns None if such a line directly precedes the line.

    Returns the line closest to the cut between the given line and the cut.
    '''
    # Travel back
    current = line
    traveled = 0
    while traveled < distance:
        current = current.prev

        current_params = current.params
        e = float(current_params.get('E', 0))
        if (current.code in ('G1', 'G0')) and (
            'Z' in current_params
            or ('E' in current_params and e <= 0)
            or (e == 0 and current.metadata.get('distance_mms', 0) > 0)
        ):
            if current.next is line:
                return None
            else:
                return current.next

        traveled += current.metadata.get('distance_mm', 0)

    # current is now the line to cut because it caused the distance to be exceeded
    current_length = current.metadata['distance_mm']
    b_length = traveled - distance
    a_length = current_length - b_length

    # prevent undesirably small segments
    if a_length < min_segment_length or b_length < min_segment_length:
        if a_length < b_length:
            return current
        else:
            return current.next

    a = Line(str(current))
    a.metadata['annotator_state'] = current.metadata['annotator_state']

    b = Line(str(current))

    a_factor = a_length / current_length
    b_factor = b_length / current_length

    a_x, a_y = (current.metadata['vector'] * a_factor) + current.metadata['start_pos']
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
