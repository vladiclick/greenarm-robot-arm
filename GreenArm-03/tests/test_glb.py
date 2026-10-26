import json,struct,unittest
from export_glb import build_glb

class GLBTests(unittest.TestCase):
    def fixture(self):
        return {'palette':{'white':(1,1,1)},'objects':[
            {'component':'test','name':'triangle','role':'structure','material':'white',
             'vertices':((0,0,0),(1000,0,0),(0,1000,0)),'triangles':((0,1,2),)}]}
    def decode(self,data):
        magic,version,total=struct.unpack_from('<4sII',data)
        self.assertEqual((magic,version,total),(b'glTF',2,len(data)))
        size,kind=struct.unpack_from('<I4s',data,12)
        self.assertEqual(kind,b'JSON')
        doc=json.loads(data[20:20+size]);offset=20+size
        length,kind=struct.unpack_from('<I4s',data,offset)
        self.assertEqual(kind,b'BIN\0')
        return doc,data[offset+8:offset+8+length]
    def test_units_orientation_and_finite_normals(self):
        doc,buffer=self.decode(build_glb(self.fixture()))
        view=doc['bufferViews'][0]
        coords=struct.unpack_from('<9f',buffer,view['byteOffset'])
        self.assertEqual(coords,(0,0,0,1,0,0,0,0,-1))
        normals=struct.unpack_from('<9f',buffer,doc['bufferViews'][1]['byteOffset'])
        self.assertEqual(normals,(0,1,0)*3)
    def test_accessors_fit_buffer_and_mesh_is_referenced(self):
        doc,buffer=self.decode(build_glb(self.fixture()))
        for view in doc['bufferViews']:
            self.assertEqual(view['byteOffset']%4,0)
            self.assertLessEqual(view['byteOffset']+view['byteLength'],len(buffer))
        group=doc['nodes'][doc['scenes'][0]['nodes'][0]]
        part=doc['nodes'][group['children'][0]]
        self.assertEqual(part['mesh'],0)
        self.assertEqual(part['extras']['role'],'structure')
        self.assertEqual(len(doc['meshes']),1)
    def test_invalid_triangle_fails(self):
        data=self.fixture();obj=dict(data['objects'][0],triangles=((0,0,0),))
        with self.assertRaises(ValueError):build_glb(dict(data,objects=[obj]))
    def test_colored_albedo_is_not_tinted_twice(self):
        fixture=self.fixture()
        scene=dict(fixture,palette={'white':(1,1,1),'green':(.7,.77,.71)})
        doc,buffer=self.decode(build_glb(scene,b'PNG texture fixture'))
        green=next(m for m in doc['materials']if m['name']=='green')
        self.assertEqual(green['pbrMetallicRoughness']['baseColorFactor'],[1,1,1,1])
        self.assertEqual(green['pbrMetallicRoughness']['baseColorTexture'],{'index':0})

if __name__=='__main__':unittest.main()
