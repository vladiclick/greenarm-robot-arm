"""Native Fusion packaging audit. Run with GreenArm 02 active."""
import adsk,adsk.core as C,adsk.fusion as F,json,os,traceback
HERE=os.path.dirname(os.path.realpath(__file__))
WORK=os.path.abspath(os.path.join(HERE,'..','..','work','greenarm'))
os.makedirs(WORK,exist_ok=True)
SERVO_NAMES=set()

def describe(entity):
    ctx=getattr(entity,'assemblyContext',None)
    parent=getattr(entity,'parentComponent',None)
    path=ctx.fullPathName if ctx else parent.name if parent else ''
    return {'body':entity.name,'path':path,
            'motor':'drawing reconstruction' in path,
            'servo':bool(parent and parent.name in SERVO_NAMES)}

def run(context):
    app=C.Application.get()
    try:
        design=F.Design.cast(app.activeProduct)
        root=design.rootComponent
        root.isJointsFolderLightBulbOn=False
        app.userInterface.activeSelections.clear()
        bodies=[]
        for occ in root.allOccurrences:
            motor='drawing reconstruction' in occ.fullPathName
            servo='SUPPLIER STEP' in occ.fullPathName
            if servo:SERVO_NAMES.add(occ.component.name)
            for body in occ.bRepBodies:
                cosmetic=any(s in body.name.lower()for s in('skin','hollow link','palm','cover','ribbon','deck','plinth'))
                if motor or servo or cosmetic:
                    bodies.append(body)
        entities=C.ObjectCollection.create()
        for body in bodies:entities.add(body)
        inp=design.createInterferenceInput(entities)
        inp.areCoincidentFacesIncluded=False
        results=design.analyzeInterference(inp)
        clashes=[]
        for result in results:
            one,two=describe(result.entityOne),describe(result.entityTwo)
            vol=result.interferenceBody.volume*1000
            if vol>.01:
                bb=result.interferenceBody.boundingBox
                clashes.append({'one':one,'two':two,'volume_mm3':vol,
                    'intersection_box_mm':[[10*getattr(pt,k)for k in('x','y','z')]for pt in(bb.minPoint,bb.maxPoint)]})
        audit={'status':'complete','scope':'All motor solids against cosmetic skins, plus cosmetic/cosmetic overlaps, at current pose only',
               'inputs':[dict(describe(b),box_mm=[[10*getattr(pt,k)for k in('x','y','z')]for pt in(b.boundingBox.minPoint,b.boundingBox.maxPoint)])for b in bodies],
               'checked_bodies':len(bodies),'motor_vs_shell':[x for x in clashes if x['one']['motor']!=x['two']['motor']],
               'servo_vs_shell':[x for x in clashes if x['one']['servo']!=x['two']['servo']],
               'cosmetic_pairs':[x for x in clashes if not x['one']['motor']and not x['two']['motor']and not x['one']['servo']and not x['two']['servo']]}
        with open(os.path.join(HERE,'Assembly-fit-audit.json'),'w')as f:json.dump(audit,f,indent=2)
        app.activeViewport.refresh()
        with open(os.path.join(WORK,'audit-progress.txt'),'w')as f:f.write('Complete')
    except Exception:
        with open(os.path.join(WORK,'audit-progress.txt'),'w')as f:f.write(traceback.format_exc())
        app.userInterface.messageBox(traceback.format_exc())
