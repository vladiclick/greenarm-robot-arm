"""Compile the same declared solids into closed meshes for independent inspection."""
from dataclasses import asdict
import json,math,os
from spec_types import PALETTE,circle_points,convex_hull,world_matrix
from design_spec import build_scene
import mesh_geometry as G

def hole_outline(hole,segments=32):
    if not hole.slot:return circle_points(hole.x,hole.y,hole.radius,segments)
    return convex_hull(circle_points(hole.x-hole.slot/2,hole.y,hole.radius,segments)+
                       circle_points(hole.x+hole.slot/2,hole.y,hole.radius,segments))

def part_mesh(part):
    if part.kind=='ring':return G.ring(*part.data,segments=64)
    if part.kind=='frame':return G.polygon_frame(*part.data)
    if part.kind=='poly':
        points,z,depth=part.data
        if part.holes:return G.extrude_with_holes(points,tuple(hole_outline(h)for h in part.holes),z,depth)
        return G.extrude_polygon(points,z,depth)
    raise ValueError('Unknown primitive '+part.kind)

def compile_scene(scene):
    objects=()
    for component in scene.components:
        matrix=world_matrix(scene,component.id)
        for index,part in enumerate(component.parts):
            try:
                local=part_mesh(part)
                mesh=G.transform_mesh(local,matrix)
                if not G.is_watertight(mesh)or G.volume(mesh)<=0:raise ValueError('Solid is not closed with positive volume')
            except Exception as exc:
                raise ValueError(component.id+' / '+part.name+': '+str(exc))from exc
            objects+=({'id':component.id+'/'+str(index),'component':component.id,'name':part.name,'role':part.role,
                'material':part.material,'vertices':mesh.vertices,'triangles':mesh.triangles,
                'volume_mm3':G.volume(mesh),'bounds_mm':G.bounds(mesh)},)
    return {'version':'GreenArm03 design review; Fusion execution pending','palette':PALETTE,
            'parameters':asdict(scene.parameters),'objects':objects}

def main():
    here=os.path.dirname(os.path.realpath(__file__))
    scene=build_scene();payload=compile_scene(scene)
    out=os.path.abspath(os.path.join(here,'..','..','work','greenarm03'));os.makedirs(out,exist_ok=True)
    with open(os.path.join(out,'meshes.json'),'w')as f:json.dump(payload,f,separators=(',',':'))
    with open(os.path.join(here,'Design-spec.json'),'w')as f:json.dump(asdict(scene),f,indent=2)
    print('Compiled',len(payload['objects']),'closed solids;',sum(len(x['triangles'])for x in payload['objects']),'triangles')

if __name__=='__main__':main()
