import sys

from parser import Parser
from filler import Polygon, Border

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('provide .igs file!')
        sys.exit(0)

    parser = Parser(sys.argv[1])
    lines = parser.lines

    if not lines:
        print('no lines found! check file')
        sys.exit(0)

    border = Border(lines)
    polygon = Polygon(lines)

    polygon.fill_ploygon(border.boundary)

    assert polygon.rectangles

    polygon.print_rectangles('out.txt')