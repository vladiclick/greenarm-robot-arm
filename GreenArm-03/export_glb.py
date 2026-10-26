"""Export the shared closed meshes as a standard, self-contained glTF 2.0 asset.

Millimetre Z-up input becomes metre Y-up glTF. A mesh preview is not native CAD.
"""
import json,math,struct
from pathlib import Path

def flatten_face(vertices,face):
    points=tuple((vertices[i][0]/1000,vertices[i][2]/1000,-vertices[i][1]/1000)for i in face)
    a,b,c=points;u=tuple(b[i]-a[i]for i in range(3));v=tuple(c[i]-a[i]for i in range(3))
    n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
    length=math.sqrt(sum(x*x for x in n))
    if length<1e-14:raise ValueError('Degenerate triangle cannot have a surface normal')
    normal=tuple(x/length for x in n)
    if not all(math.isfinite(x)for point in points for x in point):raise ValueError('Nonfinite vertex')
    axes=tuple(i for i in range(3)if i!=max(range(3),key=lambda i:abs(normal[i])))
    uv=tuple((p[axes[0]]/.06,p[axes[1]]/.06)for p in points)
    return points,normal,uv

def build_glb(scene,texture=None,internal=False):
    data=bytearray();views=[];accessors=[];meshes=[];nodes=[];groups={}
    def append_buffer(raw,target=None):
        data.extend(b'\0'*((-len(data))%4));start=len(data);data.extend(raw)
        view={'buffer':0,'byteOffset':start,'byteLength':len(raw)}
        if target:view['target']=target
        views.append(view);return len(views)-1
    def accessor(values,components,kind,component_type=5126,bounds=False,target=34962):
        raw=struct.pack('<'+('f'if component_type==5126 else'I')*len(values),*values)
        item={'bufferView':append_buffer(raw,target),'componentType':component_type,
              'count':len(values)//components,'type':kind}
        if bounds:
            item['min']=[min(values[i::components])for i in range(components)]
            item['max']=[max(values[i::components])for i in range(components)]
        accessors.append(item);return len(accessors)-1
    palette=scene['palette'];materials=[];material_ids={}
    for name,rgb in palette.items():
        pbr={'baseColorFactor':list(rgb)+[1],'metallicFactor':.7 if name in('metal','darkmetal')else 0,
             'roughnessFactor':.44 if name in('metal','darkmetal')else .78}
        if name=='green'and texture:
            pbr['baseColorFactor']=[1,1,1,1]
            pbr['baseColorTexture']={'index':0}
        material_ids[name]=len(materials);materials.append({'name':name,'pbrMetallicRoughness':pbr})
    for obj in scene['objects']:
        if internal and obj['role']=='cosmetic':continue
        positions=[];normals=[];uvs=[]
        for face in obj['triangles']:
            points,normal,uv=flatten_face(obj['vertices'],face)
            positions.extend(x for p in points for x in p)
            normals.extend(normal*3);uvs.extend(x for p in uv for x in p)
        primitive={'attributes':{'POSITION':accessor(positions,3,'VEC3',bounds=True),
                                  'NORMAL':accessor(normals,3,'VEC3'),
                                  'TEXCOORD_0':accessor(uvs,2,'VEC2')},
                   'indices':accessor(tuple(range(len(positions)//3)),1,'SCALAR',5125,target=34963),
                   'material':material_ids[obj['material']],'mode':4}
        mesh_index=len(meshes);meshes.append({'name':obj['name'],'primitives':[primitive]})
        component=obj['component']
        if component not in groups:
            groups[component]=len(nodes);nodes.append({'name':component,'children':[]})
        part_index=len(nodes);nodes.append({'name':obj['name'],'mesh':mesh_index,
                                           'extras':{'role':obj['role'],'manufacturingStatus':'development'}})
        nodes[groups[component]]['children'].append(part_index)
    document={'asset':{'version':'2.0','generator':'GreenArm03 shared geometry exporter'},
              'scene':0,'scenes':[{'nodes':list(groups.values())}],
              'nodes':nodes,'meshes':meshes,'materials':materials,'bufferViews':views,'accessors':accessors,
              'extras':{'units':'metres','nativeFusionBuild':'pending','status':'Design review, not production CAD'}}
    if texture:
        image_view=append_buffer(texture)
        document.update(images=[{'bufferView':image_view,'mimeType':'image/png'}],
                        samplers=[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}],
                        textures=[{'source':0,'sampler':0}])
    data.extend(b'\0'*((-len(data))%4));document['buffers']=[{'byteLength':len(data)}]
    encoded=json.dumps(document,separators=(',',':'),ensure_ascii=True).encode()
    encoded+=b' '*((-len(encoded))%4)
    length=12+8+len(encoded)+8+len(data)
    return struct.pack('<4sII',b'glTF',2,length)+struct.pack('<I4s',len(encoded),b'JSON')+encoded+struct.pack('<I4s',len(data),b'BIN\0')+data

def main():
    here=Path(__file__).resolve().parent
    scene=json.loads((here.parent.parent/'work/greenarm03/meshes.json').read_text())
    texture=(here/'materials/green-marble-albedo.png').read_bytes()
    for internal,name in ((False,'GreenArm-03.glb'),(True,'GreenArm-03-internal.glb')):
        result=build_glb(scene,texture,internal)
        (here/name).write_bytes(result);print(name,len(result),'bytes')

if __name__=='__main__':main()
