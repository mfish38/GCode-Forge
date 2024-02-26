
from ..parser import GCodeFile, Line, parse
from ..annotator import annotate

def apply(gcode: GCodeFile, options):
    options = {
        section_type: parse(section_gcode)
        for section_type, section_gcode in options.items()
    }

    section = gcode.first_section
    while section:
        section_gcode = options.get(section.section_type)
        if not section_gcode:
            section = section.next
            continue

        prev_section_start = section.first_line

        line_to_insert = section_gcode.first_section.last_line
        insert_before = section.first_line
        while True:
            if not line_to_insert:
                break

            section.insert_before(
                insert_before,
                line_to_insert.copy()
            )

            line_to_insert = line_to_insert.prev
            insert_before = insert_before.prev

        annotate(section.first_line.prev, prev_section_start, reannotate=True)

        section = section.next
