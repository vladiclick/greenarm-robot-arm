"""Native Fusion compiler for the shared GreenArm03 specification.

This file is prepared, not executed/validated in Fusion until app control returns.
"""
import os,json,traceback,math
import adsk,adsk.core as C,adsk.fusion as F
from design_spec import build_scene
from spec_types import PALETTE,matrix
from preview_geometry import hole_outline
from periodic_spline import periodic_controls,uniform_knots

HERE=os.path.dirname(os.path.realpath(__file__))

def point(x=0,y=0,z=0):return C.Point3D.create(x/10,y/10,z/10)
def value(mm):return C.ValueInput.createByReal(mm/10)
def collection(items):
    result=C.ObjectCollection.create()
    for item in items:result.add(item)
    return result

def plane(comp,z):
    if abs(z)<1e-10:return comp.xYConstructionPlane
    inp=comp.constructionPlanes.createInput();inp.setByOffset(comp.xYConstructionPlane,value(z))
    result=comp.constructionPlanes.add(inp);result.isLightBulbOn=False
    return result

def polygon_loop(sk,points,spline=False):
    if spline:
        controls=periodic_controls(points)
        curve=C.NurbsCurve3D.createNonRational([point(x,y)for x,y in controls],3,list(uniform_knots(controls)),False)
        if curve is None:raise RuntimeError('Cannot create closed cycloidal NURBS')
        sk.sketchCurves.sketchFixedSplines.addByNurbsCurve(curve)
    else:
        for a,b in zip(points,points[1:]+points[:1]):sk.sketchCurves.sketchLines.addByTwoPoints(point(*a),point(*b))

def compile_part(comp,part,materials):
    if part.kind=='poly':
        outer,z,depth=part.data;holes=part.holes;loop_count=1+len(holes)
    elif part.kind=='frame':
        outer,inner,z,depth=part.data;holes=();loop_count=2
    elif part.kind=='ring':
        x,y,z,r,inner_radius,depth=part.data;holes=();loop_count=2 if inner_radius else 1
    else:raise ValueError('Unknown part kind '+part.kind)
    sk=comp.sketches.add(plane(comp,z));sk.name=part.name+' | profile';sk.isComputeDeferred=True
    if part.kind=='ring':
        sk.sketchCurves.sketchCircles.addByCenterRadius(point(x,y),r/10)
        if inner_radius:sk.sketchCurves.sketchCircles.addByCenterRadius(point(x,y),inner_radius/10)
    else:
        polygon_loop(sk,outer,part.name.startswith('Cycloidal disc'))
        if part.kind=='frame':polygon_loop(sk,inner)
        for h in holes:
            if h.slot:polygon_loop(sk,hole_outline(h,32))
            else:sk.sketchCurves.sketchCircles.addByCenterRadius(point(h.x,h.y),h.radius/10)
    sk.isComputeDeferred=False
    candidates=[profile for profile in sk.profiles if profile.profileLoops.count==loop_count]
    if not candidates:raise RuntimeError('Closed profile/holes mismatch: '+part.name)
    profile=max(candidates,key=lambda p:p.areaProperties().area)
    feat=comp.features.extrudeFeatures.addSimple(profile,value(depth),F.FeatureOperations.NewBodyFeatureOperation)
    feat.name=part.name;body=feat.bodies.item(0);body.name=part.name;body.appearance=materials[part.material]
    body.attributes.add('GreenArm','role',part.role);sk.isVisible=False
    return body

def make_materials(design):
    result={}
    for key,rgb in PALETTE.items():
        appearance=design.appearances.add('GREENARM03 | '+key)
        appearance.color=C.Color.create(*(int(c*255)for c in rgb),255)
        appearance.roughness=.42 if key in('metal','darkmetal')else .72
        result[key]=appearance
    green=result['green']
    green.colorTexture=os.path.join(HERE,'materials','green-marble-albedo.png')
    green.normalTexture=os.path.join(HERE,'materials','pla-layer-normal.png')
    for slot in('opaque_albedo','surface_normal'):
        prop=green.appearanceProperties.itemById(slot);tex=getattr(prop,'value',None)
        if hasattr(tex,'properties'):
            for pid in('texture_RealWorldScaleX','texture_RealWorldScaleY'):
                scale=tex.properties.itemById(pid)
                if scale:scale.value=6.
    return result

def native_matrix(origin,angle):
    rows=matrix(origin,angle);m=C.Matrix3D.create()
    m.setWithCoordinateSystem(point(*origin),*(C.Vector3D.create(rows[0][j],rows[1][j],rows[2][j])for j in range(3)))
    return m

def attach_joints(root,occurrences,scene):
    for cid in('base','torso','upper','forearm','hand'):
        host=occurrences[cid]
        children=[c.createForAssemblyContext(host)for c in host.component.occurrences]
        if children:
            group=root.rigidGroups.add(collection([host]+children),True);group.name='Mounted hardware | '+cid
    occurrences['base'].isGrounded=True
    points={c.id:c.origin for c in scene.components}
    for first,second,anchor,axis in(('base','torso',(0,0,78),'z'),('torso','upper',points['upper'],'y'),
                                  ('upper','forearm',points['forearm'],'y'),('forearm','hand',points['hand'],'y')):
        sk=root.sketches.add(root.xYConstructionPlane)
        p=sk.sketchPoints.add(point(*anchor));geo=F.JointGeometry.createByPoint(p)
        inp=root.asBuiltJoints.createInput(occurrences[first],occurrences[second],geo)
        inp.setAsRevoluteJointMotion(F.JointDirections.ZAxisJointDirection if axis=='z'else F.JointDirections.YAxisJointDirection)
        joint=root.asBuiltJoints.add(inp);joint.name=first+' -> '+second;joint.isLightBulbOn=False;sk.isVisible=False
    root.isJointsFolderLightBulbOn=False

def snapshot(app,path):
    camera=app.activeViewport.camera;camera.isSmoothTransition=False
    camera.cameraType=C.CameraTypes.OrthographicCameraType;camera.eye=point(550,-800,430)
    camera.target=point(45,0,195);camera.upVector=C.Vector3D.create(0,0,1);camera.isFitView=True
    app.activeViewport.camera=camera;app.activeViewport.fit();app.activeViewport.refresh();adsk.doEvents()
    if not app.activeViewport.saveAsImageFile(path,2200,1800):raise RuntimeError('Fusion image export failed')

def run(context):
    app=C.Application.get();status_path=os.path.join(HERE,'Fusion-run.json')
    def log(stage,**details):
        with open(status_path,'w')as f:json.dump(dict(stage=stage,**details),f,indent=2)
        adsk.doEvents()
    try:
        scene=build_scene();log('Creating native Fusion document')
        document=app.documents.add(C.DocumentTypes.FusionDesignDocumentType);document.name='GREENARM 03 | Angular MG996R development'
        design=F.Design.cast(app.activeProduct);root=design.rootComponent;materials=make_materials(design)
        occurrences={}
        for c in scene.components:
            parent=root if c.parent is None else occurrences[c.parent].component
            occurrence=parent.occurrences.addNewComponent(native_matrix(c.origin,c.angle));occurrence.component.name=c.name
            occurrence.component.attributes.add('GreenArm','category',c.category);occurrences[c.id]=occurrence
            log('Building '+c.name)
            for part in c.parts:compile_part(occurrence.component,part,materials)
            occurrence.component.isOriginFolderLightBulbOn=False;occurrence.component.isConstructionFolderLightBulbOn=False
        attach_joints(root,occurrences,scene)
        app.userInterface.activeSelections.clear();snapshot(app,os.path.join(HERE,'GreenArm-03-Fusion.png'))
        export=design.exportManager
        if not export.execute(export.createFusionArchiveExportOptions(os.path.join(HERE,'GreenArm-03.f3d'))):raise RuntimeError('F3D export failed')
        if not export.execute(export.createSTEPExportOptions(os.path.join(HERE,'GreenArm-03.step'))):raise RuntimeError('STEP export failed')
        issues=[]
        for item in design.timeline:
            entity=item.entity
            if entity and hasattr(entity,'healthState')and entity.healthState!=F.FeatureHealthStates.HealthyFeatureHealthState:
                issues.append({'name':entity.name,'message':getattr(entity,'errorOrWarningMessage','')})
        log('Native build complete',components=root.allOccurrences.count,joints=root.asBuiltJoints.count,timeline_issues=issues,
            manufacturing_status='Development only: whole-arm fit, motion, thermal, mechanism, purchased fit and budget validation pending')
    except Exception:
        error=traceback.format_exc();log('Native build failed',error=error);app.userInterface.messageBox(error)
