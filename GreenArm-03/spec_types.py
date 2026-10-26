"""Immutable geometry shared by the Fusion generator and independent preview."""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Hole:
    x:float
    y:float
    radius:float
    slot:float=0

@dataclass(frozen=True)
class Part:
    name:str
    kind:str
    data:tuple
    material:str='green'
    role:str='cosmetic'
    holes:tuple=()

@dataclass(frozen=True)
class Component:
    id:str
    name:str
    parent:str|None
    origin:tuple=(0.,0.,0.)
    angle:float|None=None
    parts:tuple=()
    category:str='assembly'

@dataclass(frozen=True)
class Scene:
    components:tuple
    parameters:object

PALETTE={'green':(.70,.77,.71),'white':(.90,.91,.87),'graphite':(.12,.15,.14),
         'metal':(.55,.59,.58),'darkmetal':(.25,.29,.28),'gear':(.76,.75,.66),'pad':(.08,.10,.09)}

def circle_points(x,y,r,n=64,phase=0):
    return tuple((x+r*math.cos(phase+2*math.pi*k/n),y+r*math.sin(phase+2*math.pi*k/n))for k in range(n))

def chamfer_rect(cx,cy,w,h,c=2):
    if min(w,h)<=0 or c<0 or 2*c>=min(w,h):raise ValueError('Invalid rectangle/chamfer')
    x0,x1,y0,y1=cx-w/2,cx+w/2,cy-h/2,cy+h/2
    if not c:return ((x0,y0),(x1,y0),(x1,y1),(x0,y1))
    return ((x0+c,y0),(x1-c,y0),(x1,y0+c),(x1,y1-c),(x1-c,y1),(x0+c,y1),(x0,y1-c),(x0,y0+c))

def convex_hull(points):
    pts=sorted(set(points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    def half(seq):
        result=[]
        for point in seq:
            while len(result)>1 and cross(result[-2],result[-1],point)<=1e-10:result.pop()
            result.append(point)
        return result
    return tuple(half(pts)[:-1]+half(reversed(pts))[:-1])

def inset_convex(poly,offset):
    def line(a,b):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        nx,ny=-dy/length,dx/length
        return (a[0]+offset*nx,a[1]+offset*ny),(dx,dy)
    lines=tuple(line(a,b)for a,b in zip(poly,poly[1:]+poly[:1]))
    def intersect(one,two):
        (px,py),(rx,ry)=one;(qx,qy),(sx,sy)=two
        det=rx*sy-ry*sx
        if abs(det)<1e-10:raise ValueError('Parallel inset edges')
        t=((qx-px)*sy-(qy-py)*sx)/det
        return px+t*rx,py+t*ry
    return tuple(intersect(lines[i-1],lines[i])for i in range(len(poly)))

def poly(name,points,z,depth,mat='green',role='cosmetic',holes=()):
    return Part(name,'poly',(tuple(points),z,depth),mat,role,tuple(holes))

def box(name,cx,cy,z,w,h,depth,mat='green',role='cosmetic',chamfer=2,holes=()):
    return poly(name,chamfer_rect(cx,cy,w,h,chamfer),z,depth,mat,role,holes)

def ring(name,x,y,z,r,inner,depth,mat='green',role='cosmetic'):
    return Part(name,'ring',(x,y,z,r,inner,depth),mat,role)

def frame(name,outer,inner,z,depth,mat='green',role='structure'):
    return Part(name,'frame',(tuple(outer),tuple(inner),z,depth),mat,role)

def screw(name,x,y,z,depth=1.6,r=2.5):
    return poly(name,circle_points(x,y,r,6,math.pi/6),z,depth,'graphite','fastener', (Hole(x,y,.9),))

def matrix(origin,angle=None):
    x,y,z=origin
    if angle is None:return ((1.,0.,0.,x),(0.,1.,0.,y),(0.,0.,1.,z),(0.,0.,0.,1.))
    c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle))
    return ((c,-s,0.,x),(0.,0.,-1.,y),(s,c,0.,z),(0.,0.,0.,1.))

def multiply(a,b):return tuple(tuple(sum(a[i][k]*b[k][j]for k in range(4))for j in range(4))for i in range(4))

def world_matrix(scene,component_id,seen=()):
    if component_id in seen:raise ValueError('Cyclic assembly')
    comp=next(c for c in scene.components if c.id==component_id)
    local=matrix(comp.origin,comp.angle)
    return local if comp.parent is None else multiply(world_matrix(scene,comp.parent,seen+(component_id,)),local)
