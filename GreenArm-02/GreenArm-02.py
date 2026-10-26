"""Fusion Scripts entry point. Creates a new development document."""
import importlib.util
import os
import sys

def run(context):
    here=os.path.dirname(os.path.realpath(__file__))
    for name in('cad_tools','hardware','reducer','cycloid_math','periodic_spline','AssemblyAudit','FinishAssembly','ExportDetails'):
        sys.modules.pop(name,None)
    spec=importlib.util.spec_from_file_location('greenarm_builder',os.path.join(here,'GreenArm02.py'))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.run(context)
