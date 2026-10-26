"""Geometric regression checks; these are not strength or life tests."""
import math
import unittest

from cycloid_math import (
    assembly_disc_geometry,
    cycloid_points,
    minimum_roller_clearance,
    profile_point,
    validate_design,
)


class CycloidGeometryTests(unittest.TestCase):
    def test_zero_angle_profile_and_ratio(self):
        self.assertAlmostEqual(profile_point(0, 40, 5, 1.5, 12, .1)[0], 33.4)
        geometry = assembly_disc_geometry(input_angle=2 * math.pi)
        self.assertAlmostEqual(geometry['output_angle'], -2 * math.pi / 11)
        self.assertEqual(geometry['reduction_ratio'], 11)

    def test_both_discs_clear_fixed_rollers_through_rotation(self):
        for angle in (0, .17, .9, math.pi / 2, math.pi, 4.2, 2 * math.pi, 12.3):
            for phase in (0, math.pi):
                with self.subTest(angle=angle, phase=phase):
                    points = cycloid_points(40, 5, 1.5, 12, 1440, angle, phase, .1)
                    gap = minimum_roller_clearance(points, 40, 5, 12)
                    self.assertGreater(gap, .098)
                    self.assertLess(gap, .102)

    def test_second_disc_canonical_phasing(self):
        first = assembly_disc_geometry()
        second = assembly_disc_geometry(disc_phase=math.pi)
        self.assertEqual(first['eccentric_center'], (1.5, 0.0))
        self.assertAlmostEqual(second['eccentric_center'][0], -1.5)
        self.assertAlmostEqual(second['profile_orientation'], -math.pi / 11)
        self.assertAlmostEqual(second['local_hole_phase'], math.pi / 11)

    def test_identical_disc_rotated_180_is_equivalent_for_11_lobes_6_holes(self):
        def rotate(p, angle):
            return (p[0]*math.cos(angle)-p[1]*math.sin(angle),
                    p[0]*math.sin(angle)+p[1]*math.cos(angle))
        for t in (0, .1, .7, 1.9, 4.3):
            canonical = rotate(profile_point(t), -math.pi / 11)
            identical_part = rotate(profile_point(t - 12*math.pi/11), math.pi)
            self.assertLess(math.dist(canonical, identical_part), 1e-10)
        second = assembly_disc_geometry(disc_phase=math.pi)
        for hole in second['output_holes_global']:
            # Same first-part six-hole pattern, physically turned 180 degrees.
            identical_holes = tuple((-1.5 - 22*math.cos(k*math.pi/3),
                                      -22*math.sin(k*math.pi/3)) for k in range(6))
            self.assertLess(min(math.dist(hole, other) for other in identical_holes), 1e-10)

    def test_output_pins_fit_holes_for_both_discs(self):
        for angle in (0, .3, 1, 3, 6, 10):
            for phase in (0, math.pi):
                geometry = assembly_disc_geometry(input_angle=angle, disc_phase=phase)
                for hole, pin in zip(geometry['output_holes_global'], geometry['output_pins_global']):
                    gap = geometry['output_hole_radius'] - math.dist(hole, pin) - 2
                    self.assertAlmostEqual(gap, .15, places=10)

    def test_holes_have_material_to_bearing_and_rim(self):
        result = validate_design()
        self.assertTrue(result['valid'])
        self.assertGreater(result['minimum_bearing_web'], 7)
        self.assertGreater(result['conservative_rim_web'], 7)
        self.assertEqual(len(assembly_disc_geometry()['output_holes_local']), 6)

    def test_invalid_inputs_are_rejected(self):
        invalid = ({'N': 2}, {'e': 0}, {'e': 5}, {'r': -1}, {'clearance': -1}, {'samples': 10})
        for changes in invalid:
            args = dict(R=40, r=5, e=1.5, N=12, samples=720, clearance=.1)
            args.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                cycloid_points(**args)


if __name__ == '__main__':
    unittest.main(verbosity=2)
