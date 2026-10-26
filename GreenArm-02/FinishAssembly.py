"""Final native recesses and current-pose packaging report."""
import os,traceback
import adsk,adsk.core as C,adsk.fusion as F
HERE=os.path.dirname(os.path.realpath(__file__))
from cad_tools import circle,cut

def apply(root):
    upper=next(o.component for o in root.occurrences if o.component.name.startswith('03 |'))
    shell=max((b for b in upper.bRepBodies if b.name.startswith('Green Marble tapered hollow link')),key=lambda b:b.volume)
    cutter=circle(upper,165,0,-47.8,55,95.6,'Elbow decorative ribbon running clearance tool',None)
    cut(upper,shell,cutter,'Elbow ribbon clearance - 0.8mm additional axial gap')
    for host,prefix,cap_name in(('02 |','White rear torso service ribbon','Shoulder rear cap | white flush cover'),
                               ('03 |','White integrated service ribbon','Distal flush cap | white flush cover'),
                               ('04 |','White integrated service ribbon','Distal flush cap | white flush cover')):
        comp=next(o.component for o in root.occurrences if o.component.name.startswith(host))
        ribbon=next(b for b in comp.bRepBodies if b.name==prefix)
        cover=next(b for b in comp.bRepBodies if b.name==cap_name)
        cut(comp,ribbon,cover,'Separate ribbon and removable white cover interface',True)

def run(context):
    app=C.Application.get()
    try:
        design=F.Design.cast(app.activeProduct);root=design.rootComponent
        apply(root)
        from AssemblyAudit import run as audit
        audit(context)
        from GreenArm02 import camera
        camera(app,(520,-750,430),path=os.path.join(HERE,'GreenArm-02-assembled.png'))
        camera(app,(-400,650,330),path=os.path.join(HERE,'GreenArm-02-rear.png'))
        from ExportDetails import run as details
        details(context)
        camera(app,(520,-750,430))
        export=design.exportManager
        export.execute(export.createFusionArchiveExportOptions(os.path.join(HERE,'GreenArm-02.f3d')))
        export.execute(export.createSTEPExportOptions(os.path.join(HERE,'GreenArm-02.step')))
        with open(os.path.join(HERE,'Finish-status.txt'),'w')as f:f.write('Complete: added native clearances, reran fit audit, exported updated assembly and reducer detail.')
    except Exception:
        app.userInterface.messageBox(traceback.format_exc())
