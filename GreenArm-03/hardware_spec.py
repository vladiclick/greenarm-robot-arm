"""Drawing-based component references. No claim of original manufacturer STEP."""
import math
from spec_types import *

def stepper_parts(size,length,shaft,shaft_length,pitch):
    face=chamfer_rect(0,0,size,size,3 if size<50 else 4)
    pattern=tuple(Hole(i*pitch/2,j*pitch/2,1.5 if size<50 else 2.55)for i in(-1,1)for j in(-1,1))
    flat_profile=tuple((min(x,shaft/2-.5),y)for x,y in circle_points(0,0,shaft/2,48))
    flat_profile=convex_hull(flat_profile)
    return (poly('Stator casing | nominal drawing',face,-length+7,length-12,'graphite','hardware'),
        poly('Rear end bell',face,-length,7,'darkmetal','hardware'),
        poly('Front mounting flange',face,-5,5,'metal','hardware',pattern),
        ring('Pilot boss',0,0,0,11 if size<50 else 19.05,0,2,'metal','hardware'),
        poly('D output shaft | protrusion from mounting face',flat_profile,2,shaft_length-2,'metal','hardware'),
        box('Cable connector',0,-size/2-1,-length+1,12,5,8,'graphite','hardware',.8))

def mount(x,y,z,size,pitch):
    holes=(Hole(x,y,11.2 if size<50 else 19.3),)+tuple(Hole(x+i*pitch/2,y+j*pitch/2,1.6 if size<50 else 2.7)for i in(-1,1)for j in(-1,1))
    return box('Motor mount | metal, stock and holes to finalize',x,y,z,size+5,size+5,3,'metal','hardware',1,holes)

def bearing(name,x,y,z,bore,od,width):
    return (ring(name+' outer race',x,y,z,od/2,od/2-1,width,'metal','hardware'),
            ring(name+' inner race',x,y,z,bore/2+1,bore/2,width,'metal','hardware'),
            ring(name+' shield',x,y,z+.15,od/2-1,bore/2+1,width-.3,'darkmetal','hardware'))

def pulley(x,y,z,teeth,bore,width=6):
    r=teeth*2/(2*math.pi)
    return (ring(str(teeth)+'T pulley envelope | tooth profile pending',x,y,z,r+.6,bore,width,'darkmetal','hardware'),
            ring(str(teeth)+'T flange',x,y,z+width,r+1,bore,.8,'metal','hardware'))

def belt(a,b,z,r1,r2,width,name):
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
    if length<=abs(r1-r2):raise ValueError('Belt tangent impossible')
    theta=math.atan2(dy,dx);beta=math.acos((r1-r2)/length)
    result=()
    for t in(theta+beta,theta-beta):
        u=(a[0]+r1*math.cos(t),a[1]+r1*math.sin(t));v=(b[0]+r2*math.cos(t),b[1]+r2*math.sin(t))
        nx,ny=-(v[1]-u[1]),v[0]-u[0];n=math.hypot(nx,ny);nx,ny=nx/n*.65,ny/n*.65
        points=((u[0]+nx,u[1]+ny),(v[0]+nx,v[1]+ny),(v[0]-nx,v[1]-ny),(u[0]-nx,u[1]-ny))
        result+=(poly(name+' span | belt length pending',points,z,width,'graphite','hardware'),)
    return result+(ring(name+' drive wrap',*a,z,r1+.65,max(.1,r1-.65),width,'graphite','hardware'),
                   ring(name+' driven wrap',*b,z,r2+.65,max(.1,r2-.65),width,'graphite','hardware'))

def servo_parts():
    # Exact purchased variant/drawing still controls mounting pattern and shaft offset.
    ears=tuple(box('MG996R nominal ear | verify hole pattern',sign*23.675,0,26.8,6.65,20,2.5,
        'graphite','hardware',.6,tuple(Hole(sign*24.25,y,1.25)for y in(-5,5)))for sign in(-1,1))
    body=(box('MG996R case | 40.7 x 19.7 x 37 nominal',0,0,0,40.7,19.7,32,'graphite','hardware',1),
          box('MG996R top cover',0,0,32,40.7,19.7,5,'graphite','hardware',1),
          ring('MG996R boss | offset is provisional',10.35,0,37,6.5,0,2.5,'graphite','hardware'),
          ring('MG996R spline envelope | purchased fit pending',10.35,0,39.5,3,0,3.4,'metal','hardware'))
    return body+ears+tuple(screw('MG996R case screw',x,y,36.8,1,1.3)for x in(-17,17)for y in(-6,6))
