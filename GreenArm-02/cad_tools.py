"""Small native Fusion modelling helpers. Units at boundaries: millimetres."""
import math
import adsk.core as C
import adsk.fusion as F


def p(x=0,y=0,z=0):
    return C.Point3D.create(x/10,y/10,z/10)


def v(mm):
    return C.ValueInput.createByReal(mm/10)


def collection(items):
    result=C.ObjectCollection.create()
    for item in items:
        result.add(item)
    return result


def transform(origin=(0,0,0), angle=None):
    m=C.Matrix3D.create()
    if angle is None:
        m.translation=C.Vector3D.create(*(a/10 for a in origin))
    else:
        a=math.radians(angle)
        m.setWithCoordinateSystem(p(*origin),C.Vector3D.create(math.cos(a),0,math.sin(a)),
            C.Vector3D.create(-math.sin(a),0,math.cos(a)),C.Vector3D.create(0,-1,0))
    return m


def component(parent,name,origin=(0,0,0),angle=None):
    occurrence=parent.occurrences.addNewComponent(transform(origin,angle))
    occurrence.component.name=name
    return occurrence


def plane(comp,axis='z',offset=0):
    base={'z':comp.xYConstructionPlane,'x':comp.yZConstructionPlane,'y':comp.xZConstructionPlane}[axis]
    if not offset:
        return base
    inp=comp.constructionPlanes.createInput()
    inp.setByOffset(base,v(offset))
    result=comp.constructionPlanes.add(inp)
    result.isLightBulbOn=False
    return result


def sketch(comp,z=0,name='Profile'):
    result=comp.sketches.add(plane(comp,'z',z))
    result.name=name
    return result


def largest_profile(sk):
    if sk.profiles.count==0:
        raise RuntimeError('No closed profile: '+sk.name)
    return max(sk.profiles,key=lambda pr:pr.areaProperties().area)


def finish(comp,sk,depth,name,app,profile=None):
    feature=comp.features.extrudeFeatures.addSimple(profile or largest_profile(sk),v(depth),F.FeatureOperations.NewBodyFeatureOperation)
    feature.name=name
    body=feature.bodies.item(0)
    body.name=name
    if app:
        body.appearance=app
    sk.isVisible=False
    return body


def circle(comp,x,y,z,radius,depth,name,app,inner=0):
    sk=sketch(comp,z,name+' | circles')
    sk.sketchCurves.sketchCircles.addByCenterRadius(p(x,y),radius/10)
    if inner:
        sk.sketchCurves.sketchCircles.addByCenterRadius(p(x,y),inner/10)
    profile=next((pr for pr in sk.profiles if pr.profileLoops.count==2),None) if inner else None
    if inner and profile is None:
        raise RuntimeError('Annular profile missing: '+name)
    return finish(comp,sk,depth,name,app,profile)


def polygon(comp,points,z,depth,name,app,holes=()):
    sk=sketch(comp,z,name+' | profile')
    sk.isComputeDeferred=True
    points=tuple(points)
    for a,b in zip(points,points[1:]+points[:1]):
        sk.sketchCurves.sketchLines.addByTwoPoints(p(*a),p(*b))
    for x,y,r in holes:
        sk.sketchCurves.sketchCircles.addByCenterRadius(p(x,y),r/10)
    sk.isComputeDeferred=False
    return finish(comp,sk,depth,name,app)


def box(comp,center,size,name,app,fillet=0):
    x,y,z=center
    w,h,d=size
    body=polygon(comp,((x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2)),z-d/2,d,name,app)
    if fillet:
        edge_fillet(comp,body,fillet)
    return body


def edge_fillet(comp,body,radius):
    inp=comp.features.filletFeatures.createInput()
    inp.addConstantRadiusEdgeSet(collection(list(body.edges)),v(radius),True)
    return comp.features.filletFeatures.add(inp)


def cut(comp,target,tool,name,keep=False):
    inp=comp.features.combineFeatures.createInput(target,collection([tool]))
    inp.operation=F.FeatureOperations.CutFeatureOperation
    inp.isKeepToolBodies=keep
    result=comp.features.combineFeatures.add(inp)
    result.name=name
    return result.bodies.item(0)


def spline_profile(comp,axis,position,a,b,name,center=(0,0),exponent=2.8):
    """Smooth rounded rectangular section on XY or YZ plane."""
    sk=comp.sketches.add(plane(comp,axis,position))
    sk.name=name
    coords=[]
    for i in range(48):
        t=2*math.pi*i/48
        ct,st=math.cos(t),math.sin(t)
        u=center[0]+a*math.copysign(abs(ct)**(2/exponent),ct)
        w=center[1]+b*math.copysign(abs(st)**(2/exponent),st)
        world=p(position,u,w) if axis=='x' else p(u,w,position)
        coords.append(sk.modelToSketchSpace(world))
    spline=sk.sketchCurves.sketchFittedSplines.add(collection(coords))
    spline.isClosed=True
    return sk


def loft(comp,sections,name,app,axis='x'):
    """sections: (position, half-width, half-depth[, centre-u, centre-v])."""
    inp=comp.features.loftFeatures.createInput(F.FeatureOperations.NewBodyFeatureOperation)
    profiles=[]
    for i,section in enumerate(sections):
        pos,a,b=section[:3]
        center=section[3:] if len(section)==5 else (0,0)
        sk=spline_profile(comp,axis,pos,a,b,name+' | section '+str(i+1),center)
        inp.loftSections.add(largest_profile(sk))
        profiles.append(sk)
    inp.isSolid=True
    result=comp.features.loftFeatures.add(inp)
    result.name=name
    body=result.bodies.item(0)
    body.name=name
    if app:
        body.appearance=app
    for sk in profiles:
        sk.isVisible=False
    return body


def hull(comp,sections,name,app,wall=3,axis='x'):
    outer=loft(comp,sections,name,app,axis)
    inside=[tuple((s[0],s[1]-wall,s[2]-wall)+tuple(s[3:])) for s in sections[1:-1]]
    if len(inside)>1:
        inner=loft(comp,inside,name+' | cavity tool',None,axis)
        outer=cut(comp,outer,inner,name+' | hollow cavity')
        outer.appearance=app
    return outer


def holes(comp,target,z,depth,centres,radius,name):
    sk=sketch(comp,z,name+' | drilling')
    for x,y in centres:
        sk.sketchCurves.sketchCircles.addByCenterRadius(p(x,y),radius/10)
    profiles=collection(list(sk.profiles))
    inp=comp.features.extrudeFeatures.createInput(profiles,F.FeatureOperations.CutFeatureOperation)
    inp.setDistanceExtent(False,v(depth))
    inp.participantBodies=[target]
    feature=comp.features.extrudeFeatures.add(inp)
    feature.name=name
    sk.isVisible=False
    return feature


def pulley(comp,x,y,z,teeth,width,bore,app):
    pitch=2
    r=teeth*pitch/(2*math.pi)
    circle(comp,x,y,z,r+1,width,'Pulley flange '+str(teeth)+'T',app,bore)
    circle(comp,x,y,z+width,r+1,1,'Pulley upper flange '+str(teeth)+'T',app,bore)
    return r


def belt(comp,a,b,z,r1,r2,width,app,name='Enclosed timing belt route'):
    """Smooth belt envelope; pulley tooth profiles deliberately not fabricated."""
    dx,dy=b[0]-a[0],b[1]-a[1]
    length=math.hypot(dx,dy)
    theta=math.atan2(dy,dx)
    beta=math.acos((r1-r2)/length)
    angles=(theta+beta,theta-beta)
    ends=[((a[0]+r1*math.cos(t),a[1]+r1*math.sin(t)),
           (b[0]+r2*math.cos(t),b[1]+r2*math.sin(t))) for t in angles]
    for u,w in ends:
        nx,ny=-(w[1]-u[1]),w[0]-u[0]
        n=math.hypot(nx,ny)
        nx,ny=nx/n*.7,ny/n*.7
        polygon(comp,((u[0]+nx,u[1]+ny),(w[0]+nx,w[1]+ny),(w[0]-nx,w[1]-ny),(u[0]-nx,u[1]-ny)),z,width,name+' | span',app)
    # Curved wrap route represented by rings for packaging, not a working belt model.
    circle(comp,*a,z,r1+1,width,name+' | motor wrap',app,max(.1,r1-.4))
    circle(comp,*b,z,r2+1,width,name+' | driven wrap',app,max(.1,r2-.4))


def revolute(root,a,b,anchor,name,axis='y'):
    sk=root.sketches.add(root.xYConstructionPlane)
    point=sk.sketchPoints.add(p(*anchor))
    geo=F.JointGeometry.createByPoint(point)
    inp=root.asBuiltJoints.createInput(a,b,geo)
    inp.setAsRevoluteJointMotion({'y':F.JointDirections.YAxisJointDirection,'z':F.JointDirections.ZAxisJointDirection}[axis])
    j=root.asBuiltJoints.add(inp)
    j.name=name
    j.isLightBulbOn=False
    sk.isVisible=False
    return j


def rigid(root,a,b,name):
    inp=root.asBuiltJoints.createInput(a,b,None)
    inp.setAsRigidJointMotion()
    j=root.asBuiltJoints.add(inp)
    j.name=name
    j.isLightBulbOn=False
    return j
