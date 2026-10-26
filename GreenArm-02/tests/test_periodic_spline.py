import math
import unittest

from cycloid_math import cycloid_points, minimum_roller_clearance, profile_point
from periodic_spline import evaluate_periodic, periodic_controls, uniform_knots


class PeriodicSplineTests(unittest.TestCase):
    def setUp(self):
        self.n = 264
        self.points = tuple(profile_point(2 * math.pi * k / self.n) for k in range(self.n))
        self.controls = periodic_controls(self.points)

    def test_interpolation_at_integer_knots_without_phase_shift(self):
        self.assertEqual(len(self.controls), self.n + 3)
        self.assertEqual(self.controls[-3:], self.controls[:3])
        self.assertEqual(len(uniform_knots(self.controls)), len(self.controls) + 4)
        for i, expected in enumerate(self.points):
            self.assertLess(math.dist(evaluate_periodic(self.controls, 3 + i), expected), 1e-10)

    def test_position_first_and_second_derivative_closure(self):
        for derivative in (0, 1, 2):
            start = evaluate_periodic(self.controls, 3, derivative)
            end = evaluate_periodic(self.controls, self.n + 3, derivative)
            approaching = evaluate_periodic(self.controls, self.n + 3 - 1e-8, derivative)
            self.assertLess(math.dist(start, end), 1e-12)
            self.assertLess(math.dist(start, approaching), 1e-7)

    def test_dense_curve_error_and_roller_clearance(self):
        count = self.n * 16
        spline = tuple(evaluate_periodic(self.controls, 3 + self.n * k / count) for k in range(count))
        maximum_error = max(math.dist(p, profile_point(2 * math.pi * k / count)) for k, p in enumerate(spline))
        self.assertLess(maximum_error, .003)
        for angle in (0, .17, .9, math.pi / 2, math.pi, 4.2, 2 * math.pi, 12.3):
            for phase in (0, math.pi):
                alpha = angle + phase
                beta = -alpha / 11
                c, s = math.cos(beta), math.sin(beta)
                cx, cy = 1.5 * math.cos(alpha), 1.5 * math.sin(alpha)
                assembled = tuple((c*x - s*y + cx, s*x + c*y + cy) for x, y in spline)
                gap = minimum_roller_clearance(assembled)
                self.assertGreater(gap, .095)
                self.assertLess(gap, .105)

    def test_3d_interpolation(self):
        points = tuple((math.cos(k), math.sin(k), k % 3) for k in range(10))
        controls = periodic_controls(points)
        for i, point in enumerate(points):
            self.assertLess(math.dist(evaluate_periodic(controls, 3 + i), point), 1e-10)

    def test_invalid_inputs(self):
        for points in ([], [(0, 0)] * 3, [(0, 0), (1, 0), (2, 0), (0, 0)],
                       [(0, 0), (1, 0), (1, float('nan')), (0, 1)],
                       [(0, 0), (1, 0), (1, 2, 3), (0, 1)]):
            with self.subTest(points=points), self.assertRaises(ValueError):
                periodic_controls(points)
        with self.assertRaises(ValueError):
            evaluate_periodic(self.controls, 3, 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
