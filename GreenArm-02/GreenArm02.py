"""GREENARM 02. Run from Fusion Scripts/Add-ins. Research-informed prototype.

Concealed motors, original dual-disc cycloidal geometry, supplier STEP servo.
This is an engineering development CAD model, not a certified manufacturing set.
"""
import os
import sys
import json
import math
import traceback
import time
HERE=os.path.dirname(os.path.realpath(__file__))
if HERE not in sys.path:
    sys.path.insert(0,HERE)
import adsk
import adsk.core as C
import adsk.fusion as F
from cad_tools import *
from hardware import stepper,motor_mount,import_step,inspect_import,bearing
from reducer import reducer

OUT=HERE
WORK=os.path.abspath(os.path.join(HERE,'..','..','work','greenarm'))
os.makedirs(WORK,exist_ok=True)
COSMETICS=[]
MOTORS=[]
AUDIT=[]


def log(stage):
    with open(os.path.join(WORK,'progress.txt'),'w')as f:
        f.write(stage)
    C.Application.get().activeViewport.refresh()
    adsk.doEvents()


def materials(design):
    palette={'green':(184,203,190),'white':(241,240,234),'black':(36,43,40),
             'metal':(155,166,163),'darkmetal':(81,92,88),'gear':(207,176,112)}
    result={}
    for key,color in palette.items():
        app=design.appearances.add('GREENARM | '+key)
        app.color=C.Color.create(*color,255)
        app.roughness=.48 if key in('metal','darkmetal')else .64
        result[key]=app
    green=result['green']
    green.colorTexture=os.path.join(HERE,'materials','green-marble-albedo.png')
    green.normalTexture=os.path.join(HERE,'materials','pla-layer-normal.png')
    green.roughnessTexture=os.path.join(HERE,'materials','pla-roughness.png')
    for slot in('opaque_albedo','surface_normal','surface_roughness'):
        prop=green.appearanceProperties.itemById(slot)
        tex=getattr(prop,'value',None)
        if hasattr(tex,'properties'):
            for pid in('texture_RealWorldScaleX','texture_RealWorldScaleY'):
                scale=tex.properties.itemById(pid)
                if scale:
                    scale.value=6.0  # 60 mm texture tile in API centimetres
    return result


def add_stepper(comp,name,front,size,length,shaft,shaft_length,pitch,apps):
    occ=stepper(comp,name,front,size,length,shaft,shaft_length,pitch,apps)
    MOTORS.append(occ)
    return occ


def cap(comp,x,y,z,r,name,apps):
    circle(comp,x,y,z,r+.8,1.2,name+' | graphite reveal',apps['black'])
    body=circle(comp,x,y,z+1.2,r,2,name+' | white flush cover',apps['white'])
    COSMETICS.append(body)
    circle(comp,x,y,z+3.25,4,.5,name+' | recessed centre',apps['green'])


def create_base(root,apps):
    occ=component(root,'01 | Low base - concealed J1 drive')
    comp=occ.component
    # The lower plate is independent of the curved service enclosure.
    plate=loft(comp,[(0,91,76,-20,0),(4,98,82,-20,0),(8,98,82,-20,0)],'White mounting plinth',apps['white'],'z')
    holes(comp,plate,0,8,[(-82,-59),(-82,59),(42,-59),(42,59)],2.75,'Four M5 bench mounting holes')
    shell=loft(comp,[(8,98,82,-20,0),(11,98,82,-20,0),(71,94,78,-20,0),(80,89,73,-20,0)],
               'Green Marble removable base skin',apps['green'],'z')
    cavity=loft(comp,[(5,95,79,-20,0),(11,95,79,-20,0),(71,91,75,-20,0),(83,86,70,-20,0)],
                'Base open-top cavity cutter',None,'z')
    shell=cut(comp,shell,cavity,'Open base skin - separate plinth and deck')
    COSMETICS.append(shell)
    top=loft(comp,[(79,89,73,-20,0),(82,88,72,-20,0),(85,82,68,-20,0)],'White upper base deck',apps['white'],'z')
    holes(comp,top,79,6,[(0,0)],10.3,'Turntable shaft deck clearance')
    COSMETICS.append(top)
    shell=cut(comp,shell,top,'Base deck mating recess',True)
    # J1 3:1 transfer within the base; its body and shaft stay under upper deck.
    add_stepper(comp,'J1 | 17HS16-2004S1 - drawing reconstruction',(-58,0,51),42.3,40,5,23,31,apps)
    motor_mount(comp,-58,0,52,42.3,31,apps)
    r1=pulley(comp,-58,0,57,20,6,2.5,apps['metal'])
    r2=pulley(comp,0,0,57,60,6,10,apps['metal'])
    belt(comp,(-58,0),(0,0),57,r1,r2,6,apps['black'],'J1 3:1 belt - route only')
    bearing(comp,0,0,39,20,42,12,'6004 turntable bearing',apps)
    circle(comp,0,0,50,10,40,'Turntable output shaft',apps['metal'],4)
    for x,y in((-79,-57),(-79,57),(39,-57),(39,57)):
        circle(comp,x,y,-2,9,2,'TPU foot',apps['black'])
    return occ


def create_torso(root,apps,shoulder):
    occ=component(root,'02 | Torso - inboard NEMA23 and J2 reducer',shoulder,90)
    comp=occ.component
    # Torso runs down from shoulder. Motor is below and behind the axis,
    # with a parallel belt to the eccentric input; no exterior side pod.
    sections=[(-111,28,47,24,0),(-106,52,60,40,0),(-72,61,62,37,0),
              (-23,59,61,9,0),(0,51,59,0,0),(43,30,49,0,0),(48,19,36,0,0)]
    shell=hull(comp,sections,'Green Marble continuous torso skin',apps['green'],3)
    foot_trim=box(comp,(-125,0,0),(29,260,260),'Turntable running gap cutter',None)
    shell=cut(comp,shell,foot_trim,'Flat torso foot - 0.5mm deck running gap')
    tool=circle(comp,0,0,-47,52,94,'Shoulder central hinge clearance tool',None)
    shell=cut(comp,shell,tool,'Shoulder fork clearance - 94mm wide')
    COSMETICS.append(shell)
    # Rear white service ribbon follows body curvature instead of a motor box.
    rib=loft(comp,[(-103,10,2,26,-57),(-72,13,2,27,-61),(-23,14,2,8,-62),
                   (15,11,2,0,-57),(38,6,2,0,-48)],'White rear torso service ribbon',apps['white'])
    COSMETICS.append(rib)
    shell=cut(comp,shell,rib,'White torso ribbon mating recess',True)
    add_stepper(comp,'J2 | 23HS30-2804S - drawing reconstruction',(-62,35,33),57,76.5,6.35,21,47.14,apps)
    motor_mount(comp,-62,35,35,57,47.14,apps)
    r=pulley(comp,-62,35,46,20,6,3.175,apps['metal'])
    pulley(comp,0,0,46,20,6,3,apps['metal'])
    belt(comp,(-62,35),(0,0),46,r,r,6,apps['black'],'J2 short enclosed 1:1 belt - route only')
    gearbox=reducer(comp,'J2 | Original twin-disc 11:1 reducer',apps)
    # Flush symmetric joint caps hide the transmission service access.
    cap(comp,0,0,63,52,'Shoulder front cap',apps)
    cap(comp,0,0,-67,52,'Shoulder rear cap',apps)
    # Discrete backside ventilation, cut through skin; source motor heat demands it.
    for x in(-95,-87,-79,-71):
        cutter=box(comp,(x,95,0),(3,26,35),'Torso vent cutter',None)
        shell=cut(comp,shell,cutter,'Underside torso ventilation slot')
    return occ,gearbox


def create_link(root,apps,name,origin,angle,length,motor_x,compact_reducer=False):
    occ=component(root,name,origin,angle)
    comp=occ.component
    # 40 mm motor plus shaft23mm + clearances fit inside 84 mm axial section.
    a0=39 if compact_reducer else 35
    a1=40 if compact_reducer else 36
    distal_depth=55 if compact_reducer else 46
    sections=[(-30,15,24),(-23,a0-3,37),(0,a0,43),(motor_x,35,43),
              (length-35,a1,distal_depth),(length,a1,distal_depth),(length+25,15,distal_depth-10)]
    shell=hull(comp,sections,'Green Marble tapered hollow link',apps['green'],3)
    proximal_radius=52 if compact_reducer else 41
    proximal_tool=circle(comp,0,0,-25,proximal_radius,50,'Proximal reducer clearance tool',None)
    shell=cut(comp,shell,proximal_tool,'Proximal fixed reducer clearance')
    holes(comp,shell,-50,100,[(0,0)],3.5,'Coaxial input shaft pass-through')
    clear_radius,clear_half=(55,47) if compact_reducer else (48,32)
    tool=circle(comp,length,0,-clear_half,clear_radius,2*clear_half,'Distal hinge clearance tool',None)
    shell=cut(comp,shell,tool,'Distal bifurcated hinge opening')
    COSMETICS.append(shell)
    # Slim white continuous top ribbon, visually integrated with flush caps.
    ribbon=loft(comp,[(-18,5,1.8,0,38),(0,9,1.8,0,43.3),
                     (motor_x,10,1.8,0,43.3),(length-30,8,1.8,0,distal_depth+.3),
                     (length+12,3,1.8,0,distal_depth-4.5)],'White integrated service ribbon',apps['white'])
    COSMETICS.append(ribbon)
    shell=cut(comp,shell,ribbon,'White link ribbon mating recess',True)
    add_stepper(comp,'Inboard NEMA17 | 17HS16-2004S1 drawing reconstruction',(motor_x,0,13),42.3,40,5,23,31,apps)
    motor_mount(comp,motor_x,0,14,42.3,31,apps)
    r1=pulley(comp,motor_x,0,20,20,6,2.5,apps['metal'])
    driven=20 if compact_reducer else 80
    r2=pulley(comp,length,0,20,driven,6,3 if compact_reducer else 6,apps['metal'])
    belt(comp,(motor_x,0),(length,0),20,r1,r2,6,apps['black'],'Internal belt '+('1:1'if compact_reducer else'4:1')+' - route only')
    if compact_reducer:
        gearbox=reducer(comp,'J3 | Compact twin-disc 11:1 reducer',apps,True,(length,0,0))
    else:
        gearbox=None
        bearing(comp,length,0,-8,12,28,8,'Wrist independent bearing',apps)
        circle(comp,length,0,-8,6,39,'Wrist output shaft',apps['metal'],2)
    cap(comp,length,0,distal_depth+0.2,39 if compact_reducer else 30,'Distal flush cap',apps)
    # Rear service slots inboard of moving ends; detailed wiring still to design.
    for x in(motor_x-12,motor_x-4,motor_x+4,motor_x+12):
        tool=box(comp,(x,-35,0),(3,15,22),'Link vent cutter',None)
        shell=cut(comp,shell,tool,'Recessed underside ventilation')
    return occ,gearbox


def create_hand(root,apps,wrist):
    occ=component(root,'05 | Wrist - concealed ST3215 gripper',wrist,-90)
    comp=occ.component
    sections=[(-19,12,21),(-12,24,25),(0,29,27),(31,30,28),(57,27,24),(64,20,18)]
    shell=hull(comp,sections,'White wrist and servo palm',apps['white'],3)
    COSMETICS.append(shell)
    cover=loft(comp,[(0,12,1.5,0,27),(28,18,1.5,0,28.2),(54,12,1.5,0,24)],
               'Green Marble gripper service cover',apps['green'])
    COSMETICS.append(cover)
    shell=cut(comp,shell,cover,'Green palm cover mating recess',True)
    # Source STEP imported as a separate supplier reference; placement normalized
    # after its per-solid coordinates are inspected, not guessed from filename.
    servo_path=os.path.join(HERE,'vendor','Waveshare_ST3215.step')
    frame=C.Matrix3D.create()
    # Measured assembly center of this exact supplier STEP is (-13,-9.3,0) mm.
    # Set the local frame when creating the occurrence, before importing: this
    # avoids Fusion discarding nested transform overrides on timeline rebuild.
    frame.setWithCoordinateSystem(p(44,0,9.3),C.Vector3D.create(1,0,0),
        C.Vector3D.create(0,0,1),C.Vector3D.create(0,-1,0))
    servo=import_step(comp,servo_path,'SUPPLIER STEP | Waveshare ST3215 assembly',frame)
    bb=servo.component.boundingBox
    source_center=[5*(getattr(bb.minPoint,k)+getattr(bb.maxPoint,k))for k in('x','y','z')]
    if any(abs(a-b)>.1 for a,b in zip(source_center,(-13,-9.3,0))):
        raise RuntimeError('Supplier STEP coordinates changed: '+str(source_center))
    placement={'source_center_mm':source_center,'target_center_mm':[31,0,0],
        'rigid_transform_no_scale':True,'method':'Initial occurrence frame before import'}
    imported_boxes=inspect_import(servo)
    with open(os.path.join(WORK,'servo-boxes.json'),'w')as f:
        json.dump(imported_boxes,f,indent=2)
    AUDIT.append({'component':'ST3215 supplier import','bodies':imported_boxes,
                  'placement':placement,
                  'status':'Official supplier STEP, rigidly normalized inside palm; purchased variant still to verify'})
    # Supported parallel slide fingers with replaceable pads. Linkage is a
    # packaging development item; do not mistake this for validated gripping force.
    for sign in(-1,1):
        finger=loft(comp,[(55,5,8,sign*24,0),(65,5,8,sign*24,0),
                         (89,4.5,7,sign*22,0),(101,5.5,6,sign*18,0)],
                     'White parallel jaw '+str(sign),apps['white'])
        pad=box(comp,(92,sign*14.5,0),(18,3.5,12),'TPU replaceable grip pad',apps['black'],1)
    circle(comp,22,0,29.7,3,.5,'Small gripper identifier',apps['white'])
    return occ,servo


def camera(app,eye,target=(45,0,150),path=None):
    cam=app.activeViewport.camera
    cam.isSmoothTransition=False
    cam.eye=p(*eye)
    cam.target=p(*target)
    cam.upVector=C.Vector3D.create(0,0,1)
    cam.cameraType=C.CameraTypes.OrthographicCameraType
    cam.isFitView=True
    app.activeViewport.camera=cam
    app.activeViewport.fit()
    app.activeViewport.refresh()
    adsk.doEvents()
    if path:
        app.activeViewport.saveAsImageFile(path,2200,1800)


def run(context):
    app=C.Application.get()
    try:
        log('Creating GreenArm 02')
        doc=app.documents.add(C.DocumentTypes.FusionDesignDocumentType)
        doc.name='GREENARM 02 - Concealed drive study'
        design=F.Design.cast(app.activeProduct)
        root=design.rootComponent
        apps=materials(design)
        shoulder=(0,0,196)
        length1,length2=165,145
        elbow=(length1*math.cos(math.radians(67)),0,196+length1*math.sin(math.radians(67)))
        wrist=(elbow[0]+length2*math.cos(math.radians(-18)),0,elbow[2]+length2*math.sin(math.radians(-18)))
        for name,expression,unit,note in(
            ('UpperAxisSpacing','165 mm','mm','Nominal layout; edit generating sections to regenerate'),
            ('ForearmAxisSpacing','145 mm','mm','Nominal layout'),
            ('ShellWall','3 mm','mm','Prototype cosmetic wall target'),
            ('CycloidRatio','11','','Twelve ring rollers, eleven lobes'),
            ('ShoulderEccentricity','1.5 mm','mm','Original profile geometry')):
            design.userParameters.add(name,C.ValueInput.createByString(expression),unit,note)
        log('Base and yaw drive')
        base=create_base(root,apps)
        log('Torso and real cycloidal geometry')
        torso,gear=create_torso(root,apps,shoulder)
        log('Upper link and inboard elbow motor')
        upper,elbow_gear=create_link(root,apps,'03 | Upper link - inboard elbow drive',shoulder,67,length1,78,True)
        log('Forearm and concealed wrist drive')
        forearm,_=create_link(root,apps,'04 | Forearm - inboard wrist drive',elbow,-18,length2,67,False)
        log('Gripper and official supplier CAD')
        hand,servo=create_hand(root,apps,wrist)
        from FinishAssembly import apply as finish_recesses
        finish_recesses(root)
        for host in(base,torso,upper,forearm,hand):
            mounts=[child.createForAssemblyContext(host)for child in host.component.occurrences]
            if mounts:
                group=root.rigidGroups.add(collection([host]+mounts),True)
                group.name='Fixed hardware mounting | '+host.component.name
        base.isGrounded=True
        revolute(root,base,torso,(0,0,85),'J1 | Yaw - 3:1 belt','z')
        revolute(root,torso,upper,shoulder,'J2 | Shoulder - 11:1 cycloidal')
        revolute(root,upper,forearm,elbow,'J3 | Elbow - 11:1 cycloidal')
        revolute(root,forearm,hand,wrist,'J4 | Wrist - 4:1 belt')
        for occ in root.allOccurrences:
            occ.component.isOriginFolderLightBulbOn=False
            occ.component.isConstructionFolderLightBulbOn=False
            for sk in occ.component.sketches:
                sk.isVisible=False
        root.isJointsFolderLightBulbOn=False
        app.userInterface.activeSelections.clear()
        log('Checking shell and motor interference')
        from AssemblyAudit import run as fit_audit
        fit_audit(context)
        log('Visual and geometry audit')
        camera(app,(520,-750,430),path=os.path.join(OUT,'GreenArm-02-assembled.png'))
        camera(app,(-400,650,330),path=os.path.join(OUT,'GreenArm-02-rear.png'))
        # X-ray report hides only cosmetic bodies, keeping all actual hardware.
        for body in COSMETICS:
            if body.isValid:
                body.isVisible=False
        camera(app,(520,-750,430),path=os.path.join(OUT,'GreenArm-02-internal.png'))
        for body in COSMETICS:
            if body.isValid:
                body.isVisible=True
        camera(app,(520,-750,430))
        log('Exporting F3D and STEP')
        export=design.exportManager
        export.execute(export.createFusionArchiveExportOptions(os.path.join(OUT,'GreenArm-02.f3d')))
        export.execute(export.createSTEPExportOptions(os.path.join(OUT,'GreenArm-02.step')))
        issues=[]
        for i in range(design.timeline.count):
            ent=design.timeline.item(i).entity
            if ent and hasattr(ent,'healthState') and ent.healthState!=F.FeatureHealthStates.HealthyFeatureHealthState:
                issues.append({'name':ent.name,'message':getattr(ent,'errorOrWarningMessage','')})
        with open(os.path.join(OUT,'CAD-audit.json'),'w')as f:
            json.dump({'status':'success','components':root.allOccurrences.count,'joints':root.asBuiltJoints.count,
                'timeline_issues':issues,'hardware':AUDIT,'stage':'Engineering prototype; load, thermal, whole-arm collision and motion tests pending'},f,indent=2)
        log('Complete')
    except Exception:
        error=traceback.format_exc()
        with open(os.path.join(WORK,'error.txt'),'w')as f:
            f.write(error)
        log('ERROR - '+error)
        app.userInterface.messageBox(error)
