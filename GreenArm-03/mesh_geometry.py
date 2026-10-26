"""Small immutable watertight triangle primitives; coordinates have caller units.

All extrusions start at z and extend +depth. Polygon outlines are simple XY
loops without holes; polygon_frame handles one paired equal-vertex-count hole.
Faces use outward winding. Returned meshes have no material or CAD metadata.
"""
from collections import Counter
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Mesh:
    vertices: tuple
    triangles: tuple


def _finite(*values):
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
        raise ValueError('Dimensions must be finite numbers.')


def _positive(*values):
    _finite(*values)
    if min(values) <= 0:
        raise ValueError('Dimensions must be positive.')


def _cross(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def _area(points):
    return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))/2


def _intersects(a,b,c,d,epsilon=1e-10):
    def contains(p,q,r):
        return (min(p[0],q[0])-epsilon <= r[0] <= max(p[0],q[0])+epsilon and
                min(p[1],q[1])-epsilon <= r[1] <= max(p[1],q[1])+epsilon)
    x,y,u,v = _cross(a,b,c),_cross(a,b,d),_cross(c,d,a),_cross(c,d,b)
    if x*y < -epsilon and u*v < -epsilon:
        return True
    return any(abs(cross)<=epsilon and contains(p,q,r)
               for cross,p,q,r in ((x,a,b,c),(y,a,b,d),(u,c,d,a),(v,c,d,b)))


def _polygon(points):
    try:
        result=tuple(tuple(float(v) for v in point) for point in points)
    except (TypeError,ValueError) as exc:
        raise ValueError('Polygon must contain XY pairs.') from exc
    if result and result[0]==result[-1]:
        result=result[:-1]
    if len(result)<3 or any(len(p)!=2 for p in result):
        raise ValueError('Polygon requires at least three XY pairs.')
    for p in result:
        _finite(*p)
    if len(set(result))!=len(result) or abs(_area(result))<1e-10:
        raise ValueError('Polygon is degenerate or repeats a vertex.')
    n=len(result)
    for i in range(n):
        for j in range(i+1,n):
            if j==i+1 or (i==0 and j==n-1):
                continue
            if _intersects(result[i],result[(i+1)%n],result[j],result[(j+1)%n]):
                raise ValueError('Polygon self-intersects.')
    return result if _area(result)>0 else result[:1]+tuple(reversed(result[1:]))


def _triangulate(points,weak=False):
    """Ear-clipping of an already validated CCW simple polygon."""
    remaining=tuple(range(len(points)))
    triangles=()
    while len(remaining)>3:
        ear=None
        for k,b in enumerate(remaining):
            a,c=remaining[k-1],remaining[(k+1)%len(remaining)]
            if _cross(points[a],points[b],points[c])<=1e-12:
                continue
            inside=lambda p: min(_cross(points[a],points[b],p),
                                 _cross(points[b],points[c],p),
                                 _cross(points[c],points[a],p))>=-1e-12
            excluded=(points[a],points[b],points[c]) if weak else ()
            if not any(inside(points[j]) for j in remaining
                       if j not in (a,b,c) and points[j] not in excluded):
                ear=(k,(a,b,c))
                break
        if ear is None:
            raise ValueError('Cannot triangulate degenerate polygon.')
        k,triangle=ear
        triangles=triangles+(triangle,)
        remaining=remaining[:k]+remaining[k+1:]
    return triangles+(remaining,)


def extrude_polygon(points,z,depth):
    """Extrude a possibly concave simple XY polygon; no holes."""
    _finite(z)
    _positive(depth)
    outline=_polygon(points)
    n=len(outline)
    vertices=tuple((x,y,z) for x,y in outline)+tuple((x,y,z+depth) for x,y in outline)
    cap=_triangulate(outline)
    bottom=tuple((c,b,a) for a,b,c in cap)
    top=tuple((a+n,b+n,c+n) for a,b,c in cap)
    sides=tuple(tri for i in range(n) for j in ((i+1)%n,)
                for tri in ((i,j,j+n),(i,j+n,i+n)))
    return Mesh(vertices,bottom+top+sides)


def _inside(point,polygon):
    x,y=point
    return sum((a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]
               for a,b in zip(polygon,polygon[1:]+polygon[:1]))%2==1


def extrude_with_holes(outer,holes,z,depth):
    """True holed extrusion, using visible bridges and weak-polygon ear clipping.

    Holes are disjoint simple loops strictly inside outer. Winding is corrected.
    Bridge copies are mapped to shared indices, so caps and walls form one
    watertight manifold. Nested islands and touching boundaries are rejected.
    """
    _finite(z)
    _positive(depth)
    out=_polygon(outer)
    normalized=tuple(_polygon(h) for h in holes)
    if not normalized:
        return extrude_polygon(out,z,depth)
    loops=(out,)+tuple(h[:1]+tuple(reversed(h[1:])) for h in normalized)
    for i,hole in enumerate(loops[1:],start=1):
        if not all(_inside(p,out) for p in hole):
            raise ValueError('Every hole must lie strictly inside outer.')
        for other in loops[:i]:
            if any(_intersects(a,b,c,d) for a,b in zip(hole,hole[1:]+hole[:1])
                   for c,d in zip(other,other[1:]+other[:1])):
                raise ValueError('Hole boundaries intersect or touch.')
            if other is not out and (_inside(hole[0],other) or _inside(other[0],hole)):
                raise ValueError('Nested holes are unsupported.')
    points=tuple(p for loop in loops for p in loop)
    starts=tuple(sum(len(loop) for loop in loops[:i]) for i in range(len(loops)))
    indices=tuple(range(len(out)))
    bridges=()
    order=sorted(range(1,len(loops)),key=lambda i:max(p[0] for p in loops[i]),reverse=True)
    boundaries=tuple((a,b) for loop in loops for a,b in zip(loop,loop[1:]+loop[:1]))
    for loop_index in order:
        hole=loops[loop_index]
        hi=max(range(len(hole)),key=lambda k:(hole[k][0],-hole[k][1]))
        h=hole[hi]
        def visible(at):
            o=points[indices[at]]
            previous=points[indices[at-1]]
            following=points[indices[(at+1)%len(indices)]]
            # Bridge copies split a vertex into distinct angular sectors.
            # Attach only to the occurrence whose interior sector contains h.
            before=_cross(previous,o,h)
            after=_cross(o,following,h)
            convex=_cross(previous,o,following)>0
            if (min(before,after)<=1e-12 if convex else max(before,after)<=1e-12):
                return False
            midpoint=((h[0]+o[0])/2,(h[1]+o[1])/2)
            if not _inside(midpoint,out) or any(_inside(midpoint,loop) for loop in loops[1:]):
                return False
            return not any(_intersects(h,o,a,b) for a,b in boundaries+bridges
                           if h not in (a,b) and o not in (a,b))
        candidates=tuple(at for at in range(len(indices)) if visible(at))
        if not candidates:
            raise ValueError('No visible hole bridge found; change sampling or hole placement.')
        at=min(candidates,key=lambda at:math.dist(h,points[indices[at]]))
        oi=indices[at]
        walked=tuple(starts[loop_index]+(hi+k)%len(hole) for k in range(len(hole)+1))
        indices=indices[:at+1]+walked+(oi,)+indices[at+1:]
        bridges=bridges+((h,points[oi]),)
    weak_points=tuple(points[i] for i in indices)
    caps=tuple(tuple(indices[k] for k in triangle) for triangle in _triangulate(weak_points,weak=True))
    n=len(points)
    vertices=tuple((x,y,z) for x,y in points)+tuple((x,y,z+depth) for x,y in points)
    faces=tuple((c,b,a) for a,b,c in caps)+tuple((a+n,b+n,c+n) for a,b,c in caps)
    sides=tuple(triangle for start,loop in zip(starts,loops) for k in range(len(loop))
                for i,j in ((start+k,start+(k+1)%len(loop)),)
                for triangle in ((i,j,j+n),(i,j+n,i+n)))
    mesh=Mesh(vertices,faces+sides)
    if not is_watertight(mesh):
        raise ValueError('Holed triangulation did not produce a closed manifold.')
    return mesh


def polygon_frame(outer,inner,z,depth):
    """Extrude a frame; paired outlines must have same count and matching corners.

    Each outer[i] -> inner[i] connecting spoke must form a noncrossing strip.
    Independent clockwise input outlines are corrected while retaining index 0.
    """
    _finite(z)
    _positive(depth)
    out,ins=_polygon(outer),_polygon(inner)
    n=len(out)
    if len(ins)!=n or not all(_inside(p,out) for p in ins):
        raise ValueError('Inner outline must lie strictly inside and match outer vertex count.')
    if any(_intersects(a,b,c,d) for a,b in zip(out,out[1:]+out[:1])
           for c,d in zip(ins,ins[1:]+ins[:1])):
        raise ValueError('Inner and outer outlines intersect.')
    vertices=tuple((x,y,z) for x,y in out+ins)+tuple((x,y,z+depth) for x,y in out+ins)
    triangles=()
    for i in range(n):
        j=(i+1)%n
        # Triangulate each paired strip instead of assuming its quad is convex.
        quad=(out[i],out[j],ins[j],ins[i])
        if _area(quad)<=1e-12 or _intersects(quad[0],quad[3],quad[1],quad[2]):
            raise ValueError('Paired outline spokes cross or reverse.')
        indices=(i,j,n+j,n+i)
        cap=tuple(tuple(indices[k] for k in t) for t in _triangulate(quad))
        triangles=triangles+tuple((c,b,a) for a,b,c in cap)
        triangles=triangles+tuple((a+2*n,b+2*n,c+2*n) for a,b,c in cap)
        triangles=triangles+((i,j,j+2*n),(i,j+2*n,i+2*n),
                             (n+i,n+i+2*n,n+j+2*n),(n+i,n+j+2*n,n+j))
    return Mesh(vertices,triangles)


def ring(cx,cy,z,outer,inner,depth,segments=64):
    """Annular prism; inner=0 produces a solid cylinder."""
    _finite(cx,cy,z,inner)
    _positive(outer,depth)
    if inner<0 or inner>=outer or not isinstance(segments,int) or segments<3:
        raise ValueError('Require 0<=inner<outer and integer segments>=3.')
    outline=lambda radius: tuple((cx+radius*math.cos(2*math.pi*i/segments),
                                  cy+radius*math.sin(2*math.pi*i/segments)) for i in range(segments))
    return (extrude_polygon(outline(outer),z,depth) if inner==0
            else polygon_frame(outline(outer),outline(inner),z,depth))


def cylinder(cx,cy,z,radius,depth,segments=64):
    return ring(cx,cy,z,radius,0,depth,segments)


def box(cx,cy,z,width,height,depth,chamfer=0):
    """Centred XY rectangular prism, optionally with eight chamfered corners."""
    _finite(cx,cy,z,chamfer)
    _positive(width,height,depth)
    if chamfer<0 or 2*chamfer>=min(width,height):
        raise ValueError('Chamfer must be >=0 and less than half the shorter side.')
    x,y,c=width/2,height/2,chamfer
    corners=((-x,-y),(x,-y),(x,y),(-x,y)) if c==0 else (
        (-x+c,-y),(x-c,-y),(x,-y+c),(x,y-c),
        (x-c,y),(-x+c,y),(-x,y-c),(-x,-y+c))
    return extrude_polygon(tuple((cx+a,cy+b) for a,b in corners),z,depth)


def transform_mesh(mesh,matrix):
    """Apply finite invertible affine 4x4 matrix; reflections repair face winding."""
    if len(matrix)!=4 or any(len(row)!=4 for row in matrix):
        raise ValueError('Transform must be a 4x4 matrix.')
    for row in matrix:
        _finite(*row)
    if any(abs(a-b)>1e-12 for a,b in zip(matrix[3],(0,0,0,1))):
        raise ValueError('Transform must be affine.')
    a,b,c=matrix[:3]
    determinant=a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0])
    if abs(determinant)<1e-12:
        raise ValueError('Transform must be invertible.')
    vertices=tuple(tuple(sum(row[k]*p[k] for k in range(3))+row[3] for row in matrix[:3])
                   for p in mesh.vertices)
    triangles=mesh.triangles if determinant>0 else tuple((a,c,b) for a,b,c in mesh.triangles)
    return Mesh(vertices,triangles)


def volume(mesh,signed=False):
    """Signed tetrahedron-sum volume; absolute value by default."""
    def tetrahedron(indices):
        a,b,c=(mesh.vertices[i] for i in indices)
        return (a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+
                a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    result=math.fsum(tetrahedron(t) for t in mesh.triangles)
    return result if signed else abs(result)


def bounds(mesh):
    if not mesh.vertices:
        raise ValueError('Empty mesh has no bounds.')
    return (tuple(min(p[k] for p in mesh.vertices) for k in range(3)),
            tuple(max(p[k] for p in mesh.vertices) for k in range(3)))


def is_watertight(mesh):
    """Check nondegenerate indexed faces and exactly paired opposite directed edges."""
    edges=Counter((a,b) for triangle in mesh.triangles
                  for a,b in zip(triangle,triangle[1:]+triangle[:1]))
    if not edges or any(count!=1 or edges[(b,a)]!=1 for (a,b),count in edges.items()):
        return False
    for triangle in mesh.triangles:
        if len(set(triangle))!=3 or min(triangle)<0 or max(triangle)>=len(mesh.vertices):
            return False
        a,b,c=(mesh.vertices[i] for i in triangle)
        u,v=tuple(b[k]-a[k] for k in range(3)),tuple(c[k]-a[k] for k in range(3))
        if sum(x*x for x in (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]))<1e-24:
            return False
    return True
