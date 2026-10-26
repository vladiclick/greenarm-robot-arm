"""Original twin-disc geometry retained; its size is not cosmetically scaled."""
import math
from spec_types import *
from hardware_spec import bearing
from cycloid_math import assembly_disc_geometry

def reducer_parts(compact=False):
    R,r,e=(30,4,1)if compact else(40,5,1.5)
    pinr,outR,bore=(1.5,18,9.6)if compact else(2,22,10.6)
    radius=R+r+4
    bolt_holes=tuple(Hole((radius-2)*math.cos(k*math.pi/3),(radius-2)*math.sin(k*math.pi/3),1.6)for k in range(6))
    parts=(ring('Fixed ring | 12 roller stations',0,0,-14,radius,R+r+.4,28,'darkmetal','internal'),
           poly('Rear roller support',circle_points(0,0,radius),-17,3,'metal','internal',(Hole(0,0,21.1),)+bolt_holes),
           poly('Front roller support',circle_points(0,0,radius),14,3,'metal','internal',(Hole(0,0,21.1),)+bolt_holes))
    for phase,z,label in((0,-6,'A'),(math.pi,1,'B')):
        geom=assembly_disc_geometry(R=R,r=r,e=e,disc_phase=phase,output_pin_radius=pinr,
            output_radius=outR,bearing_bore_radius=bore,samples=264)
        cx,cy=geom['eccentric_center']
        holes=(Hole(cx,cy,bore),)+tuple(Hole(x,y,geom['output_hole_radius'])for x,y in geom['output_holes_global'])
        parts+=(poly('Cycloidal disc '+label+' | 11 lobes',geom['profile_global'],z,5,'gear','internal',holes),)
        parts+=bearing('Eccentric bearing '+label,cx,cy,z,10 if compact else 12,19 if compact else 21,5)
        parts+=(ring('Steel eccentric cam '+label,cx,cy,z,5 if compact else 6,3,5,'metal','hardware'),)
    for k in range(12):
        a=2*math.pi*k/12;x,y=R*math.cos(a),R*math.sin(a)
        parts+=(ring('Fixed metal roller pin '+str(k+1),x,y,-17,1.5,0,34,'metal','hardware'),)
        for z in(-6,2):parts+=bearing('693ZZ'if compact else'623ZZ',x,y,z,3,2*r,4)
    for z in(-11,8):parts+=(ring('Output carrier bridge',0,0,z,outR+5,8,3,'metal','internal'),)
    for k in range(6):
        a=2*math.pi*k/6
        parts+=(ring('Steel output pin '+str(k+1),outR*math.cos(a),outR*math.sin(a),-11,pinr,0,22,'metal','hardware'),)
    for z in(-24,11):parts+=(ring('Outboard output hub',0,0,z,15,9,13,'metal','hardware'),)
    for z in(-24,17):
        parts+=bearing('6806 output support',0,0,z,30,42,7)
        parts+=(ring('Output bearing collar',0,0,z,26,21.1,7,'darkmetal','internal'),)
    parts+=(ring('Steel input shaft',0,0,-27,3,0,58 if compact else 82,'metal','hardware'),)
    return parts
