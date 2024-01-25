
from dataclasses import dataclass

type Point2D = tuple[float, float]
type Vector2D = tuple[float, float]

@dataclass(slots=True)
class Annotation:
    '''
    Stores information added by the annotator.
    '''
    _state: list = None
    start_pos: Point2D = None
    end_pos: Point2D = None
    distance_mm: float = None
    vector: Vector2D = None
    angle_deg: float = None
    extrude_mm3: float = None
    move_type: str = None
    desired_feed_mms: float = None
    cos_theta: float = None

MOVE_PARAM_PRECISION = {
    'X': 3,
    'Y': 3,
    'F': 3,
    'E': 5,
}

PARAM_PRECISION = {
    'G0': MOVE_PARAM_PRECISION,
    'G1': MOVE_PARAM_PRECISION
}

class Line:
    '''
    Represents a file line.
    '''
    __slots__ = [
        'section',
        'annotation',
        'prev',
        'next',
        'comment',
        'code',
        'params',
        'eqparams',
        'is_move',
    ]

    def __init__(self, text):
        # Skip if copy()
        if text is None:
            return

        # What section the line belongs to
        self.section = None

        # For tracking info about the line.
        self.annotation = Annotation()

        # Linked list
        self.prev: Line = None
        self.next: Line = None

        # Parse comment
        parts = text.split(';', 1)

        if len(parts) == 2:
            self.comment = parts[1]
        else:
            self.comment = None

        # Parse remainder
        text = parts[0].strip()
        if text == '':
            self.code = None
            self.params = {}
            self.eqparams = {}
            self.is_move = False
            return

        parts = text.split()
        self.code = parts[0].upper()

        self.is_move = self.code in ('G1', 'G0')

        # Parse the parameters
        params = {}
        eqparams = {}
        for part in parts[1:]:
            if '=' in part:
                key, value = part.split('=', 1)
                eqparams[key] = value
                continue

            key = part[0].upper()
            value = part[1:]
            if value == '':
                params[key] = None
            else:
                params[key] = float(value)

        self.params = params
        self.eqparams = eqparams

    def copy(self):
        '''
        Note that annotation is intentionally not copied.
        '''
        line = Line(None)
        line.section = self.section
        line.annotation = Annotation()
        line.prev = self.prev
        line.next = self.next
        line.comment = self.comment
        line.code = self.code
        line.is_move = self.is_move
        line.params = self.params.copy()
        line.eqparams = self.eqparams.copy()

        return line

    def __repr__(self):
        return f'<Line {self}>'

    def __str__(self):
        param_precision = PARAM_PRECISION.get(self.code, {})

        params = []
        for k, v in self.params.items():
            if k in param_precision and v is not None:
                params.append(f'{k}{v:.{param_precision[k]}f}')
            else:
                v = '' if v is None else v
                params.append(f'{k}{v}')

        parts = [
            self.code,
            *params,
            *(f'{k}={'' if v is None else v}' for k, v in self.eqparams.items()),
            f';{self.comment}' if self.comment else '',
        ]
        return ' '.join(x for x in parts if x is not None)


@dataclass
class Section:
    section_type: str
    first_line: Line = None
    last_line: Line = None
    next: 'Section' = None
    prev: 'Section' = None

    def _set_first_line(self, line: Line):
        '''
        Handles adding the first line to the section.
        '''
        self.first_line = line
        self.last_line = line

        if self.prev:
            self.prev.last_line.next = line
            line.prev = self.prev.last_line

        if self.next:
            self.next.first_line.prev = line
            line.next = self.next.first_line

    def insert_before(self, place: Line, line: Line):
        '''
        Assumes the place given is in the section.

        If place is None, then the section is cleared of any existing lines and initialized with the line.
        '''
        line.section = self

        if place is None:
            self._set_first_line(line)
            return

        current_prev = place.prev

        line.next = place
        line.prev = current_prev
        place.prev = line

        if current_prev:
            current_prev.next = line

        if place is self.first_line:
            self.first_line = line

    def insert_after(self, place: Line, line: Line):
        '''
        Assumes the place given is in the section.

        If place is None, then the section is cleared of any existing lines and initialized with the line.
        '''
        line.section = self

        if place is None:
            self._set_first_line(line)
            return

        current_next = place.next

        line.next = current_next
        line.prev = place
        place.next = line

        if current_next:
            current_next.prev = line

        if place is self.last_line:
            self.last_line = line

    def remove(self, line: Line):
        '''
        Assumes the line given is in the section.
        '''
        line.section = None

        if line is self.first_line and line is self.last_line:
            self.first_line = None
            self.last_line = None
        elif line is self.first_line:
            self.first_line = line.next
        elif line is self.last_line:
            self.last_line = line.prev

        line.prev.next = line.next
        line.next.prev = line.prev

    def __repr__(self):
        return f'<Section {self.section_type}>'

    def __str__(self):
        current = self.first_line
        last = self.last_line
        parts = []
        while current is not last:
            parts.append(str(current))

            current = current.next

        parts.append(str(current))

        return '\n'.join(parts)


@dataclass
class GCodeFile:
    '''
    Represents a gcode file.
    '''
    first_section: Section

    def __repr__(self):
        return f'<GCodeFile>'

    def __str__(self):
        current = self.first_section
        parts = []
        while current:
            parts.append(str(current))

            current = current.next

        return '\n'.join(parts)

def parse(text) -> GCodeFile:
    '''
    Parses the given text into a GCodeFile.
    '''
    lines = text.splitlines()

    first_section = Section('start')
    current_section = first_section
    for line in lines:
        if line.startswith(';TYPE:'):
            section_type = line[len(';TYPE:'):].lower()

            new_section = Section(section_type)
            new_section.prev = current_section
            current_section.next = new_section
            current_section = new_section
        elif line.startswith(';LAYER_CHANGE'):
            section_type = 'layer_change'

            new_section = Section(section_type)
            new_section.prev = current_section
            current_section.next = new_section
            current_section = new_section

        current_section.insert_after(current_section.last_line, Line(line))

    return GCodeFile(first_section)
