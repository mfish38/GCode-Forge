
from itertools import chain
from dataclasses import dataclass

class Line:
    '''
    Represents a file line.
    '''
    def __init__(self, text):
        # For tracking info about the line.
        self.metadata = {}

        self.prev: Line = None
        self.next: Line = None

        parts = text.split(';', 1)

        if len(parts) == 2:
            self.comment = parts[1]
        else:
            self.comment = None

        text = parts[0].strip()
        if text == '':
            self.code = None
            self.params = {}
            self.eqparams = {}
            return

        parts = text.split()
        self.code = parts[0].upper()

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
                params[key] = value

        self.params = params
        self.eqparams = eqparams

    def __repr__(self):
        return f'<Line {self}>'

    def __str__(self):
        parts = [
            self.code,
            *(f'{k}{'' if v is None else v}' for k, v in self.params.items()),
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

def parse(text) -> list[Section]:
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
