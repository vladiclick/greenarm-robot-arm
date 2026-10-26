"""Export a real CAD reducer detail without changing the assembled arm."""
import os,json,traceback,sys
import adsk,adsk.core as C,adsk.fusion as F
HERE=os.path.dirname(os.path.realpath(__file__))
if HERE not in sys.path:sys.path.insert(0,HERE)
from cad_tools import p

def run(context):
    app=C.Application.get()
    visibility=[]
    body_visibility=[]
    camera=app.activeViewport.camera
    try:
        design=F.Design.cast(app.activeProduct)
        root=design.rootComponent
        torso=next(o for o in root.occurrences if o.component.name.startswith('02 |'))
        gear=next(o for o in torso.component.occurrences if o.component.name.startswith('J2 | Original'))
        export=design.exportManager
        export.execute(export.createSTEPExportOptions(os.path.join(HERE,'Shoulder-cycloidal-11to1.step'),gear.component))
        for o in root.occurrences:
            visibility.append((o,o.isLightBulbOn))
            o.isLightBulbOn=o==torso
        for b in torso.component.bRepBodies:
            body_visibility.append((b,b.isVisible));b.isVisible=False
        for o in torso.component.occurrences:
            visibility.append((o,o.isLightBulbOn));o.isLightBulbOn=o==gear
        for b in gear.component.bRepBodies:
            body_visibility.append((b,b.isVisible))
            z=(b.boundingBox.minPoint.z+b.boundingBox.maxPoint.z)*5
            n=b.name.lower()
            if z>7 and any(x in n for x in('support plate','carrier bridge','outboard output hub','support bearing','retention collar')):
                b.isVisible=False
        app.userInterface.activeSelections.clear()
        root.isJointsFolderLightBulbOn=False
        cam=app.activeViewport.camera
        cam.isSmoothTransition=False
        cam.cameraType=C.CameraTypes.OrthographicCameraType
        cam.eye=p(65,-260,275)
        cam.target=p(0,0,196)
        cam.upVector=C.Vector3D.create(0,0,1)
        cam.isFitView=True
        app.activeViewport.camera=cam
        app.activeViewport.fit();app.activeViewport.refresh();adsk.doEvents()
        app.activeViewport.saveAsImageFile(os.path.join(HERE,'Shoulder-cycloidal-cutaway.png'),1800,1600)
        with open(os.path.join(HERE,'Detail-export.json'),'w')as f:
            json.dump({'status':'success','reducer':'Original twin-disc 11:1, shoulder','hidden_front_parts':'Cover/support and front output carrier hidden for inspection only'},f,indent=2)
    except Exception:
        app.userInterface.messageBox(traceback.format_exc())
    finally:
        for b,value in body_visibility:
            if b.isValid:b.isVisible=value
        for o,value in visibility:
            if o.isValid:o.isLightBulbOn=value
        app.activeViewport.camera=camera
        app.activeViewport.refresh()
