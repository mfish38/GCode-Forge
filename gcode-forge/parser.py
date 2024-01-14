
from itertools import chain
from dataclasses import dataclass

class Line:
    '''
    Represents a file line.
    '''
    def __init__(self, text):
        # For tracking info about the line.
        self.metadata = {}

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
            *(f'{k}{v}' for k, v in self.params.items()),
            *(f'{k}={v}' for k, v in self.eqparams.items()),
            f';{self.comment}' if self.comment else '',
        ]
        return ' '.join(x for x in parts if x is not None)


@dataclass
class Section:
    section_type: str
    lines: list[Line]

    def __repr__(self):
        return f'<Section {self.section_type} {len(self.lines)} lines>'


@dataclass
class GCodeFile:
    sections: list[Section]

    def __repr__(self):
        return f'<GCodeFile {len(self.sections)} sections>'

    def __str__(self):
        return '\n'.join(
            str(x)
            for x in chain.from_iterable(x.lines for x in self.sections)
        )

def parse(text) -> list[Section]:
    lines = text.splitlines()

    sections = []
    current_type = ''
    current_section = []
    for line in lines:
        if line.startswith(';TYPE:'):
            sections.append(Section(current_type.lower(), current_section))
            current_section = []

            current_type = line[len(';TYPE:'):]
        elif line.startswith(';LAYER_CHANGE'):
            sections.append(Section(current_type.lower(), current_section))
            current_section = []

            current_type = 'layer_change'

        current_section.append(Line(line))

    sections.append(Section(current_type.lower(), current_section))

    return GCodeFile(sections)
