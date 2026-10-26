import unittest
from design_spec import build_scene, Parameters, world_matrix, multiply, hand_parts, link_parts

class DesignTests(unittest.TestCase):
    def test_compact_envelope_preserves_real_motor_space(self):
        p=Parameters()
        self.assertLess(p.base_width*p.base_depth, .55*196*164)
        self.assertGreaterEqual(p.beam_width,70)
        self.assertLess(p.beam_height,60)
        self.assertLess(p.beam_width,86)
    def test_selected_hardware_and_no_st3215(self):
        scene=build_scene()
        names=' '.join(c.name for c in scene.components)
        self.assertIn('MG996R',names)
        self.assertNotIn('ST3215',names)
        self.assertEqual(sum(c.category=='stepper'for c in scene.components),4)
        self.assertEqual(sum(c.category=='servo'for c in scene.components),1)
    def test_scene_identifiers_and_parents_are_consistent(self):
        scene=build_scene();ids=[c.id for c in scene.components]
        self.assertEqual(len(ids),len(set(ids)))
        for comp in scene.components:
            self.assertTrue(comp.parent is None or comp.parent in ids)
            matrix=world_matrix(scene,comp.id)
            self.assertEqual(len(matrix),4)
            self.assertEqual(matrix[3],(0.,0.,0.,1.))
    def test_invalid_lengths_fail_before_build(self):
        with self.assertRaises(ValueError):build_scene(Parameters(upper_length=100))
        with self.assertRaises(ValueError):build_scene(Parameters(base_width=-1))
    def test_motor_dimensions_are_kept_in_scene(self):
        scene=build_scene()
        for comp in scene.components:
            if comp.category=='stepper':
                self.assertTrue(any('shaft' in p.name.lower()for p in comp.parts))
                self.assertTrue(any('casing' in p.name.lower()for p in comp.parts))
    def test_frames_are_affine_and_nested(self):
        scene=build_scene()
        upper=world_matrix(scene,'upper');motor=world_matrix(scene,'motor_elbow')
        self.assertNotEqual(upper,motor)
        self.assertAlmostEqual(sum(motor[i][0]**2 for i in range(3)),1)
    def test_beam_has_open_belt_exits(self):
        for upper,length,motor in ((True,175,82),(False,155,69)):
            walls=[part for part in link_parts(Parameters(),length,motor,upper)
                   if 'beam sidewall' in part.name.lower()]
            self.assertEqual(len(walls),2)
            for part in walls:
                self.assertEqual(part.kind,'poly')
                ys=[point[1]for point in part.data[0]]
                self.assertTrue(min(ys)>=25 or max(ys)<=-25)
    def test_servo_ear_supports_clear_case_and_seat_ears(self):
        rails=[part for part in hand_parts()if 'servo ear rail' in part.name.lower()]
        self.assertEqual(len(rails),2)
        for rail in rails:
            points,z,depth=rail.data
            self.assertAlmostEqual(z+depth,-21.5+26.8)
            xs=[point[0]-38 for point in points]
            self.assertTrue(min(xs)>20.35 or max(xs)<-20.35)
            self.assertEqual(len(rail.holes),4)
    def test_gripper_pivots_have_rear_anchored_support(self):
        parts=hand_parts()
        self.assertEqual(sum('pivot support post' in p.name.lower()for p in parts),4)
        bridge=next(p for p in parts if 'pivot support bridge' in p.name.lower())
        self.assertEqual(len(bridge.holes),6)
        fingers=[p for p in parts if p.name.startswith('Straight finger')]
        self.assertTrue(all(p.data[1]+p.data[2]<=21 for p in fingers))
    def test_palm_distal_face_is_open_for_fingers(self):
        walls=[p for p in hand_parts()if p.name.startswith('MG996R palm cassette sidewall')]
        self.assertGreater(len(walls),2)
        for wall in walls:
            self.assertEqual(wall.kind,'poly')
            points=wall.data[0]
            self.assertFalse(all(x>=85.5 for x,y in points))

if __name__=='__main__':unittest.main()
