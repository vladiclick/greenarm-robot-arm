"""Autodesk Fusion Scripts entry point. Creates a new document."""
import os,sys,importlib.util

def run(context):
    here=os.path.dirname(os.path.realpath(__file__))
    if here in sys.path:sys.path.remove(here)
    sys.path.insert(0,here)
    for name in('spec_types','hardware_spec','reducer_spec','design_spec','preview_geometry','mesh_geometry',
                'cycloid_math','periodic_spline','fusion_backend'):
        sys.modules.pop(name,None)
    spec=importlib.util.spec_from_file_location('greenarm03_native',os.path.join(here,'fusion_backend.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.run(context)
