from decimal import Decimal
from copy import copy
import math

from attr import has

from consts import STEP

class Polygon():
    def __init__(self, lines):
        self._lines = lines
        self._rectangles = []

    @property
    def lines(self):
        return self._lines

    @property
    def rectangles(self):
        return self._rectangles

    def _point_in_polygon(self, point, polygon, borders):
        """определение методом луча, пущенным горизонтально
        если точка лежит на горизонтальной грани - убираем из рассмотрения
        """
        beams = [
            Line(point, Point(borders[1], point.y)),
            Line(point, Point(borders[0], point.y)),
        ]

        for beam in beams:
            intersects = 0
            for side in polygon.lines:
                if side.is_horizontal:
                    continue

                if side.has_intersection(beam):
                    intersects += 1

            if intersects % 2 == 1:
                return True


    def _point_in_rectangles(self, point, borders):
        for rec in self._rectangles:
            if rec.lines[1].point_on_line(point) or rec.lines[2].point_on_line(point):
                continue

            if self._point_in_polygon(point, rec, borders):
                return True

    def _is_point_allowed(self, point, borders):
        return self._point_in_polygon(point, self, borders) and not self._point_in_rectangles(point, borders)

    def _gen_square(self, point, borders):
        rec = Rectangle(point)

        for point in rec.points:
            if not self._is_point_allowed(point, borders):
                return

        return rec

    def _lines_polygons_intersection(self, polygons, lines):
        """detects intersection of list of lines and list of polygons
        if any line intersects side of polygon retruns True
        """
        for polygon in polygons:
            for side in polygon.lines:
                for line in lines:
                    if line.is_vertical  and side.is_vertical or line.is_horizontal and side.is_horizontal:
                        continue
                    if side.has_intersection(line) and not side.has_segment_start(line):
                        return True

    def _get_scan_line_segments(self, scan_line):
        """get allowed segments to generate squares"""
        points = []

        for side in self.lines:
            if side.is_horizontal:
                continue

            point = scan_line.intersection(side)
            if point:
                points.append(point)

        if not points:
            return []

        lines = {}
        points.sort(key=lambda p: p.x)
        # make init lines from intersections of scan_line and polygon
        for i, point in enumerate(points[1:]):
            if point.x == points[i].x or abs(point.x - points[i].x) < STEP:
                continue

            if i % 2 == 1:
                continue

            key = f'{points[i].x}:{points[i].y}, {point.x}:{point.y}'
            lines[key] = Line(points[i], point)

        for rec in self._rectangles:
            has_intersections = True
            while has_intersections:
                has_intersections = False
                keys_to_delete = set()
                temp_dict = {}
                for k, v in lines.items():
                    rec_line = Line(Point(rec.origin.x, v.p1.y), Point(rec.foreign.x, v.p1.y))
                    overlaps = v.overlap(rec_line)
                    if any(overlaps):
                        has_intersections = True

                    if overlaps[0] > 0:
                        key = f'{v.p1.x}:{v.p1.y}, {rec_line.p1.x}:{rec_line.p1.y}'
                        temp_dict[key] = Line(v.p1, rec_line.p1)
                        keys_to_delete.add(k)
                    if overlaps[1] > 0:
                        key = f'{rec_line.p2.x}:{rec_line.p2.y}, {v.p2.x}:{v.p2.y}'
                        temp_dict[key] = Line(rec_line.p2, v.p2)
                        keys_to_delete.add(k)

                if keys_to_delete:
                    lines.update(temp_dict)
                    for k in keys_to_delete:
                        del lines[k]

        return [v for v in lines.values()]

    def fill_ploygon(self, borders):
        print('starting filling')
        print('==================================')
        y = round(borders[2], 5)
        while True:
            if y > borders[3]:
                break

            scan_line = Line(Point(borders[0], y), Point(borders[1], y))
            segments = self._get_scan_line_segments(scan_line)

            for segment in segments:
                point = segment.first_segment_point_on_grid
                polygons = [self] + self._rectangles
                rec = self._gen_square(point, borders)
                if rec:
                    # generated minimal rec, try to stretch
                    tempx = copy(rec.foreign.x)
                    tempy = copy(rec.foreign.y)
                    intersectx = False
                    intersecty = False
                    # try to strech in two steps: horizontal and vertical
                    while True:
                        # temporary increase coords
                        if not intersectx:
                            tempx += STEP
                            # strech in horizontal
                            line1 = Line(Point(rec.origin.x, tempy), Point(tempx, tempy))
                            line2 = Line(Point(tempx, rec.origin.y), Point(tempx, tempy))
                            if self._lines_polygons_intersection(polygons, [line1, line2]):
                                intersectx = True
                                tempx -= STEP

                        if not intersecty:
                            # strech in vertical
                            tempy += STEP
                            line1 = Line(Point(rec.origin.x, rec.origin.y), Point(rec.origin.x, tempy))
                            line2 = Line(Point(rec.origin.x, tempy), Point(tempx, tempy))
                            line3 = Line(Point(tempx, rec.origin.y), Point(tempx, tempy))
                            if self._lines_polygons_intersection(polygons, [line1, line2, line3]):
                                intersecty = True
                                tempy -= STEP

                        if intersectx and intersecty:
                            rec.set_foreign(Point(tempx, tempy))
                            print(f'generated rectangle: {rec}')
                            self._rectangles.append(rec)
                            break

            y += STEP

        print(self.rectangles)
        print('finished')

    def print_rectangles(self, file):
        with open(file, 'w', encoding='utf8') as f:
            for rec in self.rectangles:
                f.write(f'{rec.origin.x} {rec.origin.y} {rec.foreign.x} {rec.foreign.y}\n')

class Line():
    def __init__(self, point1, point2):
        self._p1 = point1
        self._p2 = point2

    def __str__(self):
        return f'({self._p1}), ({self._p2})'

    def __eq__(self, line):
        if self.p1.x == line.p1.x and self.p1.y == line.p1.y and self.p2.x == line.p2.x and self.p2.y == line.p2.y:
            return True

        line1 = self.__swap_line(self)
        line2 = self.__swap_line(line)

        return line1.p1.x == line2.p1.x and line1.p1.y == line2.p1.y and line1.p2.x == line2.p2.x and line1.p2.y == line2.p2.y

    @property
    def p1(self):
        return self._p1

    @property
    def p2(self):
        return self._p2

    def __swap_line(self, line):
        """swap line coords to line from left to right and from bottom to top"""
        x1, x2 = line.p1.x, line.p2.x
        y1, y2 = line.p1.y, line.p2.y

        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        return Line(Point(x1, y1), Point(x2, y2))

    def point_on_line(self, point):
        line = self.__swap_line(self)
        on_horiontal = point.y == line.p1.y == line.p2.y and line.p1.x <= point.x <= line.p2.x
        on_vertical = point.x == line.p1.x == line.p2.x and line.p1.y <= point.y <= line.p2.y

        return on_horiontal or on_vertical

    def has_intersection(self, line):
        """check intersection for horizontal and vertical or vertical and horizontal"""
        line1 = self.__swap_line(self)
        line2 = self.__swap_line(line)

        hor_vert = line1.is_horizontal and line2.is_vertical and line1.p1.x <= line2.p1.x <= line1.p2.x and line2.p1.y <= line1.p1.y <= line2.p2.y
        vert_hor = line1.is_vertical and line2.is_horizontal and line1.p1.y <= line2.p1.y <= line1.p2.y and line2.p1.x <= line1.p1.x <= line2.p2.x

        hor_hor = line1.p1.y == line1.p2.y == line2.p1.y == line2.p2.y and ((min((line1.p2.x, line2.p2.x)) - max((line1.p1.x, line2.p1.x))) >= 0)
        vert_vert = line1.p1.x == line1.p2.x == line2.p1.x == line2.p2.x and ((min((line1.p2.y, line2.p2.y)) - max((line1.p1.y, line2.p1.y))) >= 0)

        return hor_vert or vert_hor or hor_hor or vert_vert

    def intersection(self, line):
        """return Point on intersection of horizontal and vvertical lines"""
        line1 = self.__swap_line(self)
        line2 = self.__swap_line(line)

        if line1.is_horizontal and line2.is_vertical and self.has_intersection(line):
            return Point(line2.p1.x, line1.p1.y)

    def overlap(self, line):
        line1 = self.__swap_line(self)
        line2 = self.__swap_line(line)

        return (
            ((line2.p1.x - line1.p1.x) > 0) and ((line1.p2.x - line2.p1.x) > 0),
            ((line1.p2.x - line2.p2.x) > 0) and ((line2.p2.x - line1.p1.x) > 0)
        )

    @property
    def first_segment_point_on_grid(self):
        """segment must be horizontal"""
        def _process(val):
            a = abs(val // STEP)
            b = abs(val) % STEP
            if val < 0:
                return -1 * a * STEP

            if b == 0:
                return a * STEP

            return (a + 1) * STEP

        if not self.is_horizontal:
            raise Exception('segment is not horizontal')

        line = self.__swap_line(self)
        return Point(_process(line.p1.x), line.p1.y)

    def has_segment_start(self, line):
        line1 = self.__swap_line(self)
        line2 = self.__swap_line(line)

        hor_vert = line1.is_horizontal and line2.is_vertical and \
            (line1.p1.y == line2.p1.y or line1.p1.y == line2.p2.y or \
             line2.p1.x == line1.p1.x or line2.p1.x == line1.p2.x)

        vert_hor = line1.is_vertical and line2.is_horizontal and (line1.p1.x == line2.p1.x or line1.p1.x == line2.p2.x)

        return hor_vert or vert_hor

    @property
    def is_horizontal(self):
        return self._p1.y == self._p2.y and self._p1.x != self._p2.x

    @property
    def is_vertical(self):
        return self._p1.x == self._p2.x and self._p1.y != self._p2.y


class Border():
    def __init__(self, lines):
        self._lines = lines
        self._points = set()

    def _lines_to_points(self):
        for line in self._lines:
            self._points.add(line.p1)
            self._points.add(line.p2)

    @property
    def boundary(self):
        def _process(val):
            border = None
            f = math.modf(val / STEP)[0]
            i = int(math.modf(val / STEP)[1])
            if f != 0:
                border = (abs(i) + 1) * (STEP)
                border *= -1 if i < 0 else 1
            else:
                border = val

            return border

        self._lines_to_points()

        x_set = set([point.x for point in self._points])
        y_set = set([point.y for point in self._points])
        xmax = max(x_set)
        xmin = min(x_set)

        ymax = max(y_set) / 10
        ymin = min(y_set)

        bx2 = _process(xmax)
        bx1 = _process(xmin)
        by2 = _process(ymax)
        by1 = _process(ymin)

        if bx1 > bx2:
            bx1, bx2 = bx2, bx1

        if by1 > by2:
            by1, by2 = by2, by1

        return bx1, bx2, by1, by2


class Point():
    def __init__(self, x, y):
        self._x = x
        self._y = y

    def __str__(self):
        return f'{self._x}, {self._y}'

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y


class Rectangle():
    def __init__(self, point):
        self._origin = point
        self._foreign = Point(point.x + STEP, point.y + STEP)

        self._points = []
        self._lines = []
        self.__calc_lines()

    def __str__(self):
        return f'Rectangle {self._lines[0]}\n{self._lines[1]}\n{self._lines[2]}\n{self._lines[3]}\n'

    def __calc_points(self):
        self._points = [
            Point(self._origin.x, self._origin.y),
            Point(self._foreign.x, self._origin.y),
            Point(self._foreign.x, self._foreign.y),
            Point(self._origin.x, self._foreign.y)
        ]

    def __calc_lines(self):
        self.__calc_points()
        self._lines = [
            Line(self._points[0], self._points[1]),
            Line(self._points[1], self._points[2]),
            Line(self._points[2], self._points[3]),
            Line(self._points[3], self._points[0]),
        ]

    @property
    def points(self):
        return self._points

    @property
    def origin(self):
        return self._origin

    @property
    def foreign(self):
        return self._foreign

    def set_foreign(self, point):
        self._foreign = point
        self.__calc_lines()

    @property
    def lines(self):
        return self._lines


if __name__ == '__main__':
    lines = [
        Line(Point(Decimal('4'), Decimal('0')), Point(Decimal('4'), Decimal('0.2'))),
        Line(Point(Decimal('4'), Decimal('0.2')), Point(Decimal('-4'), Decimal('0.2'))),
        Line(Point(Decimal('-4'), Decimal('0.2')), Point(Decimal('-4'), Decimal('0'))),
        Line(Point(Decimal('-4'), Decimal('0')), Point(Decimal('4'), Decimal('0')))
    ]

    border = Border(lines)
    polygon = Polygon(lines)

    test = False
    if test:
        print('test points not on line and on line')
        point = Point(Decimal('-4.00008'), Decimal('0.00000'))
        assert not lines[3].point_on_line(point)
        point = Point(Decimal('-3.99996'), Decimal('0.00000'))
        assert lines[3].point_on_line(point)
        point = Point(Decimal('-4'), Decimal('0.0001'))
        assert lines[2].point_on_line(point)

        print('test line intersections')
        assert lines[3].has_intersection(lines[2])
        line = Line(Point(Decimal('-2'), Decimal('0')), Point(Decimal('2'), Decimal('0')))
        assert lines[3].has_intersection(line)
        assert line.has_intersection(lines[3])

        line = Line(Point(Decimal('-4'), Decimal('0')), Point(Decimal('-4'), Decimal('0.1')))
        assert lines[2].has_intersection(line)

        line = Line(Point(Decimal('-2'), Decimal('0')), Point(Decimal('-2'), Decimal('0.1')))
        assert not lines[2].has_intersection(line)

        assert not lines[3].has_intersection(lines[1])

        line = Line(Point(Decimal('-4'), Decimal('0')), Point(Decimal('4.000008'), Decimal('0')))
        assert lines[2].has_intersection(line)

        print('testing polygon')
        assert not polygon._point_in_polygon(Point(Decimal('-4.00008'), Decimal('0.00000')), polygon, border.boundary)
        assert polygon._point_in_polygon(Point(Decimal('-4'), Decimal('0.00000')), polygon, border.boundary)
        assert polygon._point_in_polygon(Point(Decimal('-3.99998'), Decimal('0.00000')), polygon, border.boundary)
        assert polygon._point_in_polygon(Point(Decimal('-3.99998'), Decimal('0.00012')), polygon, border.boundary)

        print('testing beam intersections')
        line1 = Line(Point(Decimal('-2'), Decimal('0')), Point(Decimal('-2'), Decimal('0.2')))
        line2 = Line(Point(Decimal('-3'), Decimal('0.1')), Point(Decimal('2'), Decimal('0.1')))
        point = line2.intersection(line1)
        assert point and point.x == Decimal('-2') and point.y == Decimal('0.1')

        line = Line(Point(Decimal('-4'), Decimal('0')), Point(Decimal('4'), Decimal('0')))
        point = line.first_segment_point_on_grid
        assert point and point.x == Decimal('-3.99996')
        line = Line(Point(Decimal('-3.99996'), Decimal('0')), Point(Decimal('4'), Decimal('0')))
        point = line.first_segment_point_on_grid
        assert point and point.x == Decimal('-3.99996')
        line = Line(Point(Decimal('3'), Decimal('0')), Point(Decimal('4'), Decimal('0')))
        point = line.first_segment_point_on_grid
        assert point and point.x == Decimal('3')
        line = Line(Point(Decimal('3.0001'), Decimal('0')), Point(Decimal('4'), Decimal('0')))
        point = line.first_segment_point_on_grid
        assert point and point.x == Decimal('3.00012')


        lines = [
            Line(Point(Decimal('4'), Decimal('0')), Point(Decimal('4'), Decimal('0.2'))),
            Line(Point(Decimal('4'), Decimal('0.2')), Point(Decimal('-4'), Decimal('0.2'))),
            Line(Point(Decimal('-4'), Decimal('0.2')), Point(Decimal('-4'), Decimal('0'))),
            Line(Point(Decimal('-4'), Decimal('0')), Point(Decimal('2'), Decimal('0'))),
            Line(Point(Decimal('2'), Decimal('0')), Point(Decimal('2'), Decimal('-0.1'))),
            Line(Point(Decimal('2'), Decimal('-0.1')), Point(Decimal('3'), Decimal('-0.1'))),
            Line(Point(Decimal('3'), Decimal('-0.1')), Point(Decimal('3'), Decimal('0'))),
            Line(Point(Decimal('3'), Decimal('0')), Point(Decimal('4'), Decimal('0'))),
        ]

        border = Border(lines)
        polygon = Polygon(lines)
        rec = Rectangle(Point(Decimal('2.00004'), Decimal('-0.09996')))
        rec.set_foreign(Point(Decimal('3'), Decimal('0.19992')))

        polygon._rectangles.append(
            rec
        )

        scan_line = Line(Point(Decimal('-4.00008'), Decimal('0')), Point(Decimal('4.00008'), Decimal('0')))
        assert len(polygon._get_scan_line_segments(scan_line)) == 2

        scan_line = Line(Point(Decimal('-4.00008'), Decimal('0.1')), Point(Decimal('4.00008'), Decimal('0.1')))
        assert len(polygon._get_scan_line_segments(scan_line)) == 2


    else:
        # polygon.fill_ploygon(border.boundary)

        # assert len(polygon.rectangles) == 1
        # print(polygon.rectangles)
        # polygon.print_rectangles('out.txt')

        lines = [
            Line(Point(Decimal('4'), Decimal('0')), Point(Decimal('4'), Decimal('0.2'))),
            Line(Point(Decimal('4'), Decimal('0.2')), Point(Decimal('-4'), Decimal('0.2'))),
            Line(Point(Decimal('-4'), Decimal('0.2')), Point(Decimal('-4'), Decimal('0'))),
            Line(Point(Decimal('-4'), Decimal('0')), Point(Decimal('2'), Decimal('0'))),
            Line(Point(Decimal('2'), Decimal('0')), Point(Decimal('2'), Decimal('-0.1'))),
            Line(Point(Decimal('2'), Decimal('-0.1')), Point(Decimal('3'), Decimal('-0.1'))),
            Line(Point(Decimal('3'), Decimal('-0.1')), Point(Decimal('3'), Decimal('0'))),
            Line(Point(Decimal('3'), Decimal('0')), Point(Decimal('4'), Decimal('0'))),
        ]

        border = Border(lines)
        polygon = Polygon(lines)

        polygon.fill_ploygon(border.boundary)

        assert len(polygon.rectangles) == 3