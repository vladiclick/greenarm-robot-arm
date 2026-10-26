"""Original dual-disc 11:1 reducer CAD from documented normal-offset geometry."""
import math
import adsk.core as C
from cad_tools import component,circle,sketch,finish,collection,p,holes
from hardware import bearing
from cycloid_math import assembly_disc_geometry,validate_design
from periodic_spline import periodic_controls,uniform_knots


def reducer(parent,name,apps,compact=False,origin=(0,0,0)):
    occ=component(parent,name,origin)
    comp=occ.component
    R,r,e=(30,4,1) if compact else(40,5,1.5)
    pinr,outR,bore=(1.5,18,9.6) if compact else(2,22,10.6)
    radius=R+r+4
    circle(comp,0,0,-14,radius,28,'Fixed ring - twelve roller stations',apps['white'],R+r+.4)
    rear=circle(comp,0,0,-17,radius,3,'Rear pin support plate',apps['white'],21.1)
    front=circle(comp,0,0,14,radius,3,'Front pin support plate',apps['white'],21.1)
    bolt_circle=[((radius-2)*math.cos(k*math.pi/3),(radius-2)*math.sin(k*math.pi/3))for k in range(6)]
    holes(comp,rear,-17,3,bolt_circle,1.6,'Housing M3 rear fasteners')
    holes(comp,front,14,3,bolt_circle,1.6,'Housing M3 front fasteners')
    # The opposite-phase eccentric bearings and the shared output pin circle
    # follow the tested math module. All clearances are prototype allowances.
    for phase,z,label in((0,-6,'A'),(math.pi,1,'B')):
        geom=assembly_disc_geometry(R=R,r=r,e=e,disc_phase=phase,
            output_pin_radius=pinr,output_radius=outR,bearing_bore_radius=bore,samples=264)
        sk=sketch(comp,z,'Disc '+label+' | cycloidal profile')
        sk.isComputeDeferred=True
        controls=periodic_controls(geom['profile_global'])
        # Full mathematical knot vector + repeated controls closes C2 without
        # Autodesk's separate periodic flag (which expects a shorter vector).
        curve=C.NurbsCurve3D.createNonRational([p(x,y)for x,y in controls],3,list(uniform_knots(controls)),False)
        if curve is None:
            raise RuntimeError('Failed to create periodic cycloidal NURBS')
        sk.sketchCurves.sketchFixedSplines.addByNurbsCurve(curve)
        for x,y in geom['output_holes_global']:
            sk.sketchCurves.sketchCircles.addByCenterRadius(p(x,y),geom['output_hole_radius']/10)
        cx,cy=geom['eccentric_center']
        sk.sketchCurves.sketchCircles.addByCenterRadius(p(cx,cy),bore/10)
        sk.isComputeDeferred=False
        finish(comp,sk,5,'Cycloidal disc '+label+' | 11 lobes',apps['gear'])
        bearing(comp,cx,cy,z,10 if compact else 12,19 if compact else 21,5,'Eccentric input bearing '+label,apps)
        circle(comp,cx,cy,z,5 if compact else 6,5,'Steel eccentric cam '+label,apps['metal'],3)
    for k in range(12):
        a=2*math.pi*k/12
        x,y=R*math.cos(a),R*math.sin(a)
        circle(comp,x,y,-17,1.5,34,'Fixed steel roller pin '+str(k+1),apps['metal'])
        for z in(-6,2):
            bearing(comp,x,y,z,3,2*r,4,('693ZZ'if compact else'623ZZ')+' ring roller',apps)
    # Output pin bridges tie both ends, reducing pin cantilever deflection.
    for z in(-11,8):
        circle(comp,0,0,z,outR+5,3,'Output carrier bridge',apps['darkmetal'],8)
    for k in range(6):
        a=2*math.pi*k/6
        circle(comp,outR*math.cos(a),outR*math.sin(a),-11,pinr,22,'Steel output pin '+str(k+1),apps['metal'])
    for z in(-24,11):
        circle(comp,0,0,z,15,13,'Outboard output hub - central pack kept clear',apps['metal'],9)
    for z in(-24,17):
        bearing(comp,0,0,z,30,42,7,'6806 output support bearing',apps)
        circle(comp,0,0,z,26,7,'Output bearing retention collar',apps['white'],21.1)
    circle(comp,0,0,-27,3,82,'Input shaft - steel machining required',apps['metal'])
    comp.attributes.add('Reducer','ratio','11:1')
    comp.attributes.add('Reducer','validation','Geometric prototype, not torque/backlash certified')
    comp.attributes.add('Reducer','geometry',str(validate_design(R=R,r=r,e=e,output_radius=outR,
        output_pin_radius=pinr,bearing_bore_radius=bore)))
    return occ
