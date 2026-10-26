"""Hardware models: drawing-based motors and supplier STEP servo.

The motor reconstructions are explicitly not certified vendor STEP geometry.
Critical interfaces follow supplier nominal drawings; verify purchased units.
"""
import os
import math
import adsk.core as C
import adsk.fusion as F
from cad_tools import component,box,circle,polygon,holes,cut,p,collection


def stepper(parent,name,front,size,length,shaft,shaft_length,pitch,apps):
    occ=component(parent,name,front)
    comp=occ.component
    half=size/2
    k=3 if size<50 else 4
    outline=((-half+k,-half),(half-k,-half),(half,-half+k),(half,half-k),
             (half-k,half),(-half+k,half),(-half,half-k),(-half,-half+k))
    polygon(comp,outline,-length+7,length-12,name+' | stator casing',apps['black'])
    polygon(comp,outline,-length,7,name+' | rear end bell',apps['metal'])
    frontplate=polygon(comp,outline,-5,5,name+' | front flange',apps['metal'])
    hole_r=1.5 if size<50 else 2.55
    holes(comp,frontplate,-5,5,[(i*pitch/2,j*pitch/2) for i in(-1,1) for j in(-1,1)],hole_r,'Mounting pattern - drawing nominal')
    circle(comp,0,0,0,11 if size<50 else 19.05,2,'Pilot boss',apps['metal'])
    sh=circle(comp,0,0,2,shaft/2,shaft_length,'Output shaft',apps['metal'])
    flat=box(comp,(shaft/2,0,2+shaft_length/2),(1.0,shaft+1,shaft_length),'D-flat cutter',None)
    cut(comp,sh,flat,'D shaft flat')
    # Distinct outlet and flexible cable route; not a claimed internal motor model.
    box(comp,(0,-half-1,-length+5),(12,5,8),'Motor cable connector',apps['black'],.8)
    comp.attributes.add('Provenance','status','Supplier drawing reconstruction; NOT original supplier STEP')
    return occ


def import_step(parent,path,name,initial_frame=None):
    occ=component(parent,name) if initial_frame is None else parent.occurrences.addNewComponent(initial_frame)
    occ.component.name=name
    opts=C.Application.get().importManager.createSTEPImportOptions(path)
    opts.isViewFit=False
    if not C.Application.get().importManager.importToTarget(opts,occ.component):
        raise RuntimeError('STEP import failed: '+path)
    return occ


def all_bodies(comp):
    bodies=list(comp.bRepBodies)
    for occ in comp.occurrences:
        bodies.extend(all_bodies(occ.component))
    return bodies


def inspect_import(occ):
    """Per-solid native boxes for audit. Assembly world boxes need proxies."""
    result=[]
    for body in all_bodies(occ.component):
        bb=body.boundingBox
        result.append({'name':body.name,'size_mm':[10*(getattr(bb.maxPoint,k)-getattr(bb.minPoint,k)) for k in('x','y','z')],
                       'min_mm':[10*getattr(bb.minPoint,k) for k in('x','y','z')],
                       'max_mm':[10*getattr(bb.maxPoint,k) for k in('x','y','z')]})
    return result


def bearing(comp,x,y,z,bore,od,width,name,apps):
    # Standard nominal bearing, intentionally not a vendor-certified detailed model.
    circle(comp,x,y,z,od/2,width,name+' | outer race',apps['metal'],od/2-1)
    circle(comp,x,y,z,bore/2+1,width,name+' | inner race',apps['metal'],bore/2)
    circle(comp,x,y,z+.15,od/2-1,width-.3,name+' | shield',apps['darkmetal'],bore/2+1)


def motor_mount(comp,x,y,z,size,pitch,apps):
    plate=box(comp,(x,y,z),(size+9,size+9,3),'Aluminium motor mount - machining required',apps['metal'],1)
    holes(comp,plate,z-1.5,3,[(x,y)],11.2 if size<50 else 19.3,'Motor pilot clearance')
    holes(comp,plate,z-1.5,3,[(x+i*pitch/2,y+j*pitch/2)for i in(-1,1)for j in(-1,1)],1.6 if size<50 else 2.7,'Motor mount bolts')
    return plate
