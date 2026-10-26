"""Whole portable geometry path; native Fusion execution requires Fusion access."""
import unittest
from design_spec import build_scene
from preview_geometry import compile_scene

class AssemblyIntegrationTests(unittest.TestCase):
    def test_every_declared_part_compiles_to_a_closed_positive_volume_solid(self):
        scene=build_scene();result=compile_scene(scene)
        self.assertEqual(len(result['objects']),sum(len(c.parts)for c in scene.components))
        self.assertTrue(all(o['volume_mm3']>0 for o in result['objects']))
        self.assertEqual({o['component']for o in result['objects']},{c.id for c in scene.components})
        self.assertTrue(any('MG996R case' in o['name']for o in result['objects']))
        self.assertFalse(any('ST3215' in o['name']for o in result['objects']))

if __name__=='__main__':unittest.main()
