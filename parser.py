from decimal import Decimal

from filler import Line, Point


class Parser():
    def __init__(self, file):
        self._filename = file

        self._lines = []

    @property
    def lines(self):
        if not self._lines:
            self._get_lines()

        return self._lines

    def _get_lines(self):
        with open(self._filename, encoding='utf8') as fp:
            for line in fp:
                if line.startswith('110') and 'P    ' in line:
                    coords = self._get_2d_coords(line)

                    line = Line(
                            Point(coords['x1'], coords['y1']),
                            Point(coords['x2'], coords['y2'])
                        )

                    if self._can_add_line(line):
                        self._lines.append(line)


    def _get_2d_coords(self, line):
        line_ = line.split(';')[0]
        arr = line_.split(',')[1:]

        arr[2] = None
        arr[5] = None

        arr = list(filter(lambda d: d, arr))
        arr = [Decimal(i) for i in arr]

        return {'x1': arr[0], 'y1': arr[1], 'x2': arr[2], 'y2': arr[3]}

    def _can_add_line(self, line):
        for e_line in self._lines:
            if line == e_line:
                return

        if line.p1.x == line.p2.x and line.p1.y == line.p2.y:
            return

        return True