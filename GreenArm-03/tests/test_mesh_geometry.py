import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mesh_geometry import (Mesh, bounds, box, cylinder, extrude_polygon,
                           extrude_with_holes, is_watertight, polygon_frame, ring, transform_mesh, volume)


class MeshGeometryTests(unittest.TestCase):
    def assertSolid(self, mesh, expected_volume):
        self.assertTrue(is_watertight(mesh))
        self.assertAlmostEqual(volume(mesh), expected_volume, places=7)
        self.assertGreater(volume(mesh, signed=True), 0)

    def test_concave_extrusion_and_clockwise_correction(self):
        profile = ((0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3))
        for points in (profile, tuple(reversed(profile))):
            mesh = extrude_polygon(points, 2, 4)
            self.assertSolid(mesh, 20)
            self.assertEqual(bounds(mesh), ((0, 0, 2), (3, 3, 6)))

    def test_annulus_and_cylinder(self):
        n = 64
        polygon_factor = n * math.sin(2*math.pi/n) / 2
        self.assertSolid(ring(1, 2, 3, 5, 2, 4, n), polygon_factor * (25-4) * 4)
        self.assertSolid(cylinder(1, 2, 3, 5, 4, n), polygon_factor * 25 * 4)

    def test_chamfer_box(self):
        mesh = box(0, 0, -1, 10, 8, 3, chamfer=1)
        self.assertSolid(mesh, (80-2)*3)
        self.assertEqual(bounds(mesh), ((-5, -4, -1), (5, 4, 2)))

    def test_square_frame(self):
        outer = ((-3,-3),(3,-3),(3,3),(-3,3))
        inner = ((-1,-1),(1,-1),(1,1),(-1,1))
        self.assertSolid(polygon_frame(outer, inner, 0, 2), 64)
        self.assertSolid(polygon_frame(tuple(reversed(outer)), tuple(reversed(inner)), 0, 2), 64)

    def test_transform_and_reflection_preserve_outward_normals(self):
        mesh = box(0,0,0,2,4,6)
        matrix = ((-1,0,0,10),(0,1,0,20),(0,0,1,30),(0,0,0,1))
        shifted = transform_mesh(mesh, matrix)
        self.assertSolid(shifted, 48)
        self.assertEqual(bounds(shifted), ((9,18,30),(11,22,36)))

    def test_true_multiple_holes_in_cycloidal_disc(self):
        sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'work'/'greenarm'))
        from cycloid_math import profile_point
        outer=tuple(profile_point(2*math.pi*i/264) for i in range(264))
        circle=lambda x,y,r: tuple((x+r*math.cos(-2*math.pi*k/24),
                                    y+r*math.sin(-2*math.pi*k/24)) for k in range(24))
        holes=(circle(0,0,10.6),)+tuple(circle(22*math.cos(k*math.pi/3),
                                             22*math.sin(k*math.pi/3),3.65) for k in range(6))
        mesh=extrude_with_holes(outer,holes,0,5)
        area=lambda p: abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1]))/2)
        self.assertSolid(mesh,(area(outer)-sum(area(h) for h in holes))*5)

    def test_holed_square_and_invalid_holes(self):
        outer=((-3,-3),(3,-3),(3,3),(-3,3))
        inner=((-1,-1),(1,-1),(1,1),(-1,1))
        self.assertSolid(extrude_with_holes(outer,(inner,),0,2),64)
        outside=((10,10),(11,10),(11,11),(10,11))
        with self.assertRaises(ValueError):
            extrude_with_holes(outer,(outside,),0,2)

    def test_actual_motor_mount_with_central_bore_and_four_bolts(self):
        from hardware_spec import mount
        from preview_geometry import hole_outline
        for size,pitch in ((42,31),(57,47.14)):
            part=mount(0,0,0,size,pitch)
            outer,z,depth=part.data
            holes=tuple(hole_outline(h) for h in part.holes)
            mesh=extrude_with_holes(outer,holes,z,depth)
            area=lambda p: abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1]))/2)
            self.assertSolid(mesh,(area(outer)-sum(area(h) for h in holes))*depth)

    def test_invalid_inputs_fail(self):
        calls = (lambda: ring(0,0,0,2,3,1), lambda: cylinder(0,0,0,1,-1),
                 lambda: extrude_polygon(((0,0),(2,2),(0,2),(2,0)),0,1),
                 lambda: box(0,0,0,4,4,2,chamfer=3),
                 lambda: cylinder(0,0,float('nan'),1,1),
                 lambda: ring(0,0,0,2,1,1,segments=2))
        for call in calls:
            with self.assertRaises(ValueError):
                call()
        mesh=box(0,0,0,1,1,1)
        with self.assertRaises(ValueError):
            transform_mesh(mesh, ((0,0,0,0),)*4)
        self.assertFalse(is_watertight(Mesh(mesh.vertices, mesh.triangles[:-1])))


if __name__ == '__main__':
    unittest.main(verbosity=2)
