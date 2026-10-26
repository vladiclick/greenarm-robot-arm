"""GreenArm03: flat-sided concealed-drive layout; one source for previews/Fusion."""
from dataclasses import dataclass
import math
from spec_types import *
from hardware_spec import stepper_parts,mount,bearing,pulley,belt,servo_parts
from reducer_spec import reducer_parts

@dataclass(frozen=True)
class Parameters:
    upper_length:float=175
    forearm_length:float=155
    shoulder_height:float=190
    base_height:float=78
    base_width:float=130
    base_depth:float=116
    beam_width:float=73
    beam_height:float=56
    wall:float=2.5

def caps(x,y,z,r,name):
    return (ring(name+' recessed graphite seam',x,y,z,r+1,0,.7,'graphite'),
        ring(name+' narrow white annulus',x,y,z+.7,r+.7,r-.7,1.3,'white'),
        poly(name+' flat Green Marble face',circle_points(x,y,r-1,64),z+.7,1.4,'green','cosmetic',
            tuple(Hole(x+(r-6)*math.cos(k*math.pi/3),y+(r-6)*math.sin(k*math.pi/3),1.65)for k in range(6))))+tuple(
        screw(name+' flush M3 head',x+(r-6)*math.cos(k*math.pi/3),y+(r-6)*math.sin(k*math.pi/3),z+2.15,.6,2.25)for k in range(6))

def base_parts(p):
    outer=chamfer_rect(-26,0,p.base_width,p.base_depth,10)
    inner=inset_convex(outer,p.wall)
    mount_holes=tuple(Hole(x,y,2.75)for x in(-79,27)for y in(-46,46))
    parts=(poly('White bench mounting plate',outer,0,4,'white','structure',mount_holes),
           frame('Faceted base enclosure',outer,inner,4,70,'green','cosmetic'),
           poly('Flat white base deck',outer,74,4,'white','cosmetic',(Hole(0,0,10.4),)),
           mount(-52,0,47,42.3,31))
    parts+=pulley(-52,0,55,20,2.5)+pulley(0,0,55,60,10)
    parts+=belt((-52,0),(0,0),55,20/math.pi,60/math.pi,6,'J1 3:1')
    parts+=bearing('6004 turntable',0,0,35,20,42,12)
    parts+=(ring('Yaw output shaft',0,0,42,10,4,40,'metal','hardware'),)
    parts+=tuple(ring('TPU mounting foot',x,y,-2,7,0,2,'pad','pad')for x in(-78,26)for y in(-45,45))
    parts+=tuple(screw('Base service screw',x,y,78,1,2.4)for x in(-78,26)for y in(-43,43))
    return parts

def torso_parts(p):
    outer=convex_hull(circle_points(0,0,53,48)+((-110,-19),(-110,35),(-96,57),(-96,-15)))
    inner=inset_convex(outer,p.wall)
    plate_hole=(Hole(0,0,50.5),)
    parts=(frame('Straight-sided torso frame',outer,inner,-55,113,'green','structure'),
           poly('Flat rear torso panel',outer,-55,2.5,'green','cosmetic',plate_hole),
           poly('Flat front torso panel',outer,55.5,2.5,'green','cosmetic',plate_hole),
           mount(-62,20,31.5,57,47.14))
    parts+=pulley(-62,20,43,20,3.175)+pulley(0,0,43,20,3)
    parts+=belt((-62,20),(0,0),43,20/math.pi,20/math.pi,6,'J2 1:1 enclosed')
    parts+=caps(0,0,58.4,50,'Shoulder front')+caps(0,0,-58,50,'Shoulder rear')
    parts+=(box('Narrow white torso service rail',-68,-19,58.15,63,3,1.1,'white','cosmetic',.6),)
    parts+=tuple(screw('Torso panel screw',x,y,58,1,2.2)for x,y in((-99,18),(-90,-13),(-40,-36),(-40,39)))
    return parts

def link_parts(p,length,motor_x,upper):
    # The motor bay has a truthful 73mm width; thin circular forks are separate.
    x0=52 if upper else 42
    x1=length-47
    outer=chamfer_rect((x0+x1)/2,0,x1-x0,p.beam_height,3)
    vent_holes=tuple(Hole(x,y,1.3,6)for x in(motor_x-9,motor_x,motor_x+9)for y in(-12,12))
    # Open axial ends let both belt spans reach the next joint without crossing a wall.
    parts=tuple(box('Straight beam sidewall '+str(sign),(x0+x1)/2,
                    sign*(p.beam_height-p.wall)/2,-31,x1-x0,p.wall,73,
                    'green','structure',.6)for sign in(-1,1))
    parts+=(
           poly('Rear removable beam panel',outer,-31,2.5,'green','cosmetic',vent_holes),
           poly('Front removable beam panel',outer,39.5,2.5,'green','cosmetic'),
           mount(motor_x,0,14,42.3,31))
    # Separate thin fork cheeks leave the middle free for stationary reducers.
    root_radius=51 if upper else 40
    root_outline=convex_hull(circle_points(0,0,root_radius,48)+((x0+17,-23),(x0+17,23)))
    for z in(-36,42):
        parts+=(poly('Proximal bearing cheek',root_outline,z,5,'white','structure',(Hole(0,0,15.15),)),)
    # The remote motor drive runs inside the long straight beam.
    tooth=20 if upper else 80
    parts+=pulley(motor_x,0,20,20,2.5)+pulley(length,0,20,tooth,3 if upper else 6)
    parts+=belt((motor_x,0),(length,0),20,20/math.pi,tooth/math.pi,6,'Internal 1:1'if upper else'Internal 4:1')
    end_radius=40 if upper else 30
    end_outline=convex_hull(circle_points(length,0,end_radius+2,48)+((x1-10,-23),(x1-10,23)))
    # Fork cheeks sit outside the next assembly's axial envelope.
    for z in((-42,48)if upper else(-36,42)):
        parts+=(poly('Distal flat fork cheek',end_outline,z,5,'green','structure',(Hole(length,0,15.2),)),)
    parts+=caps(length,0,53.3 if upper else 47.3,end_radius,'Elbow'if upper else'Wrist')
    parts+=(box('Thin white longitudinal rail',(x0+x1)/2,-25,42.15,x1-x0-8,2.4,1.1,'white','cosmetic',.6),)
    parts+=tuple(screw('Beam service fastener',x,y,42,1,2.1)for x in(x0+7,x1-7)for y in(-21,21))
    for z,depth in((-31,7),(24,23)):
        parts+=(ring('Output coupling sleeve | fastener detail pending',0,0,z,15,9,depth,'darkmetal','hardware'),)
    if not upper:
        parts+=bearing('6001 independent wrist support',length,0,-8,12,28,8)
        parts+=(ring('Wrist output spindle',length,0,-8,6,2,39,'metal','hardware'),)
    return parts

def finger_parts(sign):
    y=sign*12
    points=((72,y-5),(78,y-5),(110,y-4),(116,y-1),(116,y+5),(110,y+7),(78,y+5),(72,y+5))
    return (poly('Straight finger '+str(sign),points,16,5,'white','structure',(Hole(75,y,1.6),)),
        box('Replaceable TPU gripping pad '+str(sign),107,y-sign*5.5,16.4,14,2.6,4.2,'pad','pad',.6))

def servo_support_parts():
    # Separate rails clear the entire case; top is exactly the nominal ear underside.
    parts=()
    for sign in(-1,1):
        x=38+sign*24.75
        holes=tuple(Hole(38+sign*24.25,y,1.5,2.5)for y in(-5,5))
        holes+=tuple(Hole(x,y,1.1)for y in(-10,10))
        parts+=(box('Servo ear rail | adjustable, purchased fit pending',x,0,2.8,7.5,26,2.5,
                    'darkmetal','hardware',.5,holes),)
        for y in(-10,10):
            parts+=(ring('Servo rail support post',x,y,-22.5,2.5,1.1,25.3,'white','structure'),)
    return parts

def pivot_support_parts():
    mounts=tuple((x,y)for x in(69,81)for y in(-18,18))
    holes=tuple(Hole(x,y,1.1)for x,y in mounts)+tuple(Hole(75,y,3.05)for y in(-12,12))
    parts=(box('Finger pivot support bridge',75,0,6,20,46,3,'darkmetal','hardware',1,holes),)
    parts+=tuple(ring('Finger pivot support post',x,y,-22.5,2.8,1.1,28.5,'white','structure')for x,y in mounts)
    parts+=tuple(ring('Finger plain bushing | fit pending',75,y,5.5,3,1.55,4.5,'metal','hardware')for y in(-12,12))
    return parts

def hand_parts():
    outline=convex_hull(((-16,-14),(-16,14),(11,-17),(61,-17),(67,-27),(88,-27),(88,27),(67,27),(61,17),(11,17)))
    inner=inset_convex(outline,2.5)
    # The main body is a compact flat cassette, not a rounded palm/blob.
    # Omit the distal end wall: fingers leave through a real open face.
    walls=tuple(poly('MG996R palm cassette sidewall '+str(i),
                     (a,b,inner[(i+1)%len(inner)],inner[i]),-25,56,'white','structure')
                for i,(a,b)in enumerate(zip(outline,outline[1:]+outline[:1]))
                if not(a[0]==88 and b[0]==88))
    parts=walls+(
           poly('Palm rear service panel',outline,-25,2.5,'white','cosmetic'),
           poly('Flat Green Marble palm cover',outline,28.5,2.5,'green','cosmetic'))
    parts+=servo_support_parts()+pivot_support_parts()
    parts+=finger_parts(-1)+finger_parts(1)
    parts+=tuple(screw('Palm service screw',x,y,31,1,2.1)for x,y in((-9,-9),(-9,9),(64,-22),(64,22)))
    # Coupled finger gears are packaging envelopes: tooth/linkage design pending.
    # Rear-panel posts support a separate bored bridge; exact fits remain pending.
    for sign in(-1,1):
        parts+=(ring('Finger pivot shaft',75,sign*12,5,1.5,0,19,'metal','hardware'),
                ring('Finger gear envelope | meshing geometry pending',75,sign*12,11,11.6,1.6,4,'darkmetal','internal'))
    parts+=(ring('Servo horn to pulley adapter | spline and fastener pending',48.35,0,19,5.2,3,3,'metal','hardware'),)
    parts+=pulley(48.35,0,22,20,3,4)+pulley(75,12,22,20,1.5,4)
    parts+=belt((48.35,0),(75,12),22,20/math.pi,20/math.pi,4,'Gripper servo drive | routing study')
    return parts

def build_scene(p=Parameters()):
    if min(p.base_width,p.base_depth,p.wall,p.beam_height,p.beam_width)<=0:raise ValueError('Positive dimensions required')
    if p.upper_length<165 or p.forearm_length<145:raise ValueError('Insufficient spacing for concealed motors/forks')
    shoulder=(0,0,p.shoulder_height)
    elbow=(p.upper_length*math.cos(math.radians(67)),0,p.shoulder_height+p.upper_length*math.sin(math.radians(67)))
    wrist=(elbow[0]+p.forearm_length*math.cos(math.radians(-18)),0,elbow[2]+p.forearm_length*math.sin(math.radians(-18)))
    comps=(Component('base','01 | Compact faceted base',None,parts=base_parts(p)),
        Component('torso','02 | Flat-sided NEMA23 pedestal',None,shoulder,90,torso_parts(p)),
        Component('upper','03 | Straight upper beam',None,shoulder,67,link_parts(p,p.upper_length,82,True)),
        Component('forearm','04 | Straight forearm beam',None,elbow,-18,link_parts(p,p.forearm_length,69,False)),
        Component('hand','05 | MG996R gripper cassette',None,wrist,-90,hand_parts()),
        Component('motor_yaw','J1 | NEMA17 drawing reference','base',(-52,0,46),parts=stepper_parts(42.3,40,5,23,31),category='stepper'),
        Component('motor_shoulder','J2 | NEMA23 drawing reference','torso',(-62,20,30),parts=stepper_parts(57,76.5,6.35,21,47.14),category='stepper'),
        Component('motor_elbow','J3 | NEMA17 drawing reference','upper',(82,0,13),parts=stepper_parts(42.3,40,5,23,31),category='stepper'),
        Component('motor_wrist','J4 | NEMA17 drawing reference','forearm',(69,0,13),parts=stepper_parts(42.3,40,5,23,31),category='stepper'),
        Component('servo','MG996R Robot 180 | drawing reconstruction, fit pending','hand',(38,0,-21.5),parts=servo_parts(),category='servo'),
        Component('reducer_shoulder','11:1 twin-disc shoulder | original geometry','torso',parts=reducer_parts()),
        Component('reducer_elbow','11:1 twin-disc elbow | original geometry','upper',(p.upper_length,0,0),parts=reducer_parts(True)))
    return Scene(comps,p)
