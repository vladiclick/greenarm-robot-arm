"""CleanArm 01 — Fusion native CAD packaging concept, NOT fabrication release.
Run inside Autodesk Fusion. Creates a new document and exports local F3D/STEP.
All dimensions in millimetres at the helper boundary; Fusion uses centimetres.
"""
import math
import os
import traceback
import json
import adsk.core
import adsk.fusion

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(OUT, 'CleanArm-build.json')
WARNINGS = []


def pt(x=0, y=0, z=0):
    return adsk.core.Point3D.create(x / 10, y / 10, z / 10)


def val(mm):
    return adsk.core.ValueInput.createByReal(mm / 10)


def component(root, name, origin=(0, 0, 0), tilt=None):
    m = adsk.core.Matrix3D.create()
    if tilt is None:
        m.translation = adsk.core.Vector3D.create(*(n / 10 for n in origin))
    else:
        a = math.radians(tilt)
        m.setWithCoordinateSystem(pt(*origin),
            adsk.core.Vector3D.create(math.cos(a), 0, math.sin(a)),
            adsk.core.Vector3D.create(-math.sin(a), 0, math.cos(a)),
            adsk.core.Vector3D.create(0, -1, 0))
    occ = root.occurrences.addNewComponent(m)
    occ.component.name = name
    return occ


def sketch(comp, z, name):
    plane = comp.xYConstructionPlane
    if abs(z) > 1e-8:
        inp = comp.constructionPlanes.createInput()
        inp.setByOffset(plane, val(z))
        plane = comp.constructionPlanes.add(inp)
        plane.isLightBulbOn = False
    sk = comp.sketches.add(plane)
    sk.name = name
    return sk


def extrude(comp, sk, depth, name, appearance, fillet=0):
    feature = comp.features.extrudeFeatures.addSimple(sk.profiles.item(0), val(depth),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    feature.name = name
    body = feature.bodies.item(0)
    body.name = name
    sk.isVisible = False
    if fillet:
        try:
            edges = adsk.core.ObjectCollection.create()
            for edge in body.edges:
                edges.add(edge)
            inp = comp.features.filletFeatures.createInput()
            inp.addConstantRadiusEdgeSet(edges, val(fillet), True)
            comp.features.filletFeatures.add(inp)
        except Exception as exc:
            WARNINGS.append(f'{name}: edge fillet omitted: {exc}')
    body.appearance = appearance
    return body


def box(comp, center, size, name, appearance, fillet=1):
    x, y, z = center
    w, h, d = size
    sk = sketch(comp, z - d / 2, name + ' profile')
    sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(x - w/2, y - h/2), pt(x + w/2, y + h/2))
    return extrude(comp, sk, d, name, appearance, fillet)


def disk(comp, x, y, z, radius, depth, name, appearance, inner=0):
    sk = sketch(comp, z, name + ' profile')
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(x, y), radius / 10)
    if inner:
        sk.sketchCurves.sketchCircles.addByCenterRadius(pt(x, y), inner / 10)
        # The annular profile has two loops; the central profile has one.
        profile = next(p for p in sk.profiles if p.profileLoops.count == 2)
        feature = comp.features.extrudeFeatures.addSimple(profile, val(depth),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        body = feature.bodies.item(0)
        body.name = name
        body.appearance = appearance
        sk.isVisible = False
        return body
    return extrude(comp, sk, depth, name, appearance)


def capsule(comp, length, r0, r1, z, depth, name, appearance):
    sk = sketch(comp, z, name + ' profile')
    arcs = sk.sketchCurves.sketchArcs
    lines = sk.sketchCurves.sketchLines
    sweep = math.copysign(math.pi, length)
    arcs.addByCenterStartSweep(pt(0, 0), pt(0, r0), sweep)
    lines.addByTwoPoints(pt(0, -r0), pt(length, -r1))
    arcs.addByCenterStartSweep(pt(length, 0), pt(length, -r1), sweep)
    lines.addByTwoPoints(pt(length, r1), pt(0, r0))
    return extrude(comp, sk, depth, name, appearance, min(1.2, depth / 3))


def appearance(design, name, color):
    source = next((a for a in design.appearances), None)
    if source is None:
        app = adsk.core.Application.get()
        for library in app.materialLibraries:
            source = next((a for a in library.appearances
                           if 'Plastic' in a.name and 'Matte' in a.name), None)
            if source:
                break
    if source is None:
        raise RuntimeError('No appearance library available')
    result = design.appearances.addByCopy(source, name)
    prop = result.appearanceProperties.itemById('opaque_albedo')
    if prop is None:
        prop = next((p for p in result.appearanceProperties
                     if isinstance(p, adsk.core.ColorProperty)), None)
    if prop:
        prop.value = adsk.core.Color.create(*color, 255)
    return result


def motor(comp, size, length, z, name, graphite, metal, x=0):
    body = box(comp, (x, 0, z + length/2), (size, size, length),
               name + ' ENVELOPE - hidden', graphite, 1)
    body.isVisible = False
    shaft = disk(comp, x, 0, z - 15, 2.5 if size == 42 else 3.175,
                 15, name + ' shaft envelope - hidden', metal)
    shaft.isVisible = False


def joint(root, a, b, anchor, name, axis):
    sk = root.sketches.add(root.xYConstructionPlane)
    point = sk.sketchPoints.add(pt(*anchor))
    geom = adsk.fusion.JointGeometry.createByPoint(point)
    inp = root.asBuiltJoints.createInput(a, b, geom)
    inp.setAsRevoluteJointMotion(axis)
    j = root.asBuiltJoints.add(inp)
    j.name = name
    j.isLightBulbOn = False
    sk.isVisible = False
    return j


def build(design):
    root = design.rootComponent
    white = appearance(design, '01 | Ceramic white', (222, 224, 218))
    black = appearance(design, '02 | Graphite matte', (39, 44, 48))
    metal = appearance(design, '03 | Satin steel', (140, 151, 156))
    accent = appearance(design, '04 | Signal amber', (245, 156, 55))
    for name, expression, note in (
        ('WallTarget', '3 mm', 'Target shell wall; packaging concept'),
        ('UpperLinkNominal', '120 mm', 'Joint centre spacing; regenerate for new layout'),
        ('ForearmNominal', '110 mm', 'Joint centre spacing; regenerate for new layout'),
        ('PayloadTarget', '500 g', 'UNVERIFIED target, not a rating')):
        unit = 'g' if 'g' == expression.split()[-1] else 'mm'
        design.userParameters.add(name, adsk.core.ValueInput.createByString(expression), unit, note)

    base = component(root, '01 | Fixed base')
    c = base.component
    disk(c, 0, 0, 0, 72, 5, 'Lower graphite plinth', black)
    disk(c, 0, 0, 5, 70, 31, 'Base enclosure - wall 3mm', white, 67)
    disk(c, 0, 0, 36, 70, 3, 'Removable upper deck', white, 23)
    disk(c, 0, 0, 39, 53, 2, 'Turntable shadow gap', black, 23)
    motor(c, 42, 40, 0, 'NEMA17 base', black, metal)
    for x, y in ((-46,-46),(46,-46),(-46,46),(46,46)):
        disk(c, x, y, -2, 7, 2, 'Elastomer foot', black)

    pedestal = component(root, '02 | Rotating shoulder pedestal')
    c = pedestal.component
    disk(c, 0, 0, 41, 50, 8, 'Rotating platform', white)
    # Fork sides, transformed as subcomponents through a rigid assembly.
    box(c, (0, 0, 64), (62, 58, 30), 'Pedestal structural bridge', white, 5)
    shoulder = (0, 0, 92)
    frame = component(root, '03 | Shoulder fork and NEMA23 housing', shoulder, 90)
    c = frame.component
    for z in (-34, 28):
        capsule(c, -35, 35, 23, z, 6, 'Shoulder fork cheek', white)
    disk(c, 0, 0, 34, 37, 24, 'Shoulder reducer ENVELOPE', black, 12)
    disk(c, 0, 0, 58, 35, 3, 'Shoulder service cap', white)
    disk(c, 0, 0, 61, 10, 1, 'Shoulder hub detail', black)
    box(c, (0, 0, -76), (72, 72, 80), 'NEMA23 shroud ENVELOPE', white, 6)
    motor(c, 57, 76.5, -114, 'NEMA23 shoulder', black, metal)

    a = math.radians(65)
    elbow = (120*math.cos(a), 0, 92+120*math.sin(a))
    wrist = (elbow[0]+110*math.cos(math.radians(-20)), 0,
             elbow[2]+110*math.sin(math.radians(-20)))
    upper = component(root, '04 | Upper arm - 120mm', shoulder, 65)
    c = upper.component
    capsule(c, 120, 26, 23, -25, 50, 'Upper arm shell ENVELOPE', white)
    capsule(c, 84, 12, 10, 25.2, 1.8, 'Upper graphite service panel', black)
    disk(c, 0, 0, 27.2, 18, 2, 'Shoulder output hub', black)
    disk(c, 120, 0, 25, 25, 20, 'Elbow gearbox ENVELOPE', black)
    disk(c, 120, 0, 45, 23, 3, 'Elbow clean cap', white)
    disk(c, 120, 0, 48, 7, 1, 'Elbow hub detail', black)
    box(c, (100, 0, -51), (52, 52, 46), 'Elbow motor shroud ENVELOPE', white, 4)
    # Hardware envelopes remain hidden and separately named.
    motor(c, 42, 40, -71, 'NEMA17 elbow provisional', black, metal, 100)

    forearm = component(root, '05 | Forearm - 110mm', elbow, -20)
    c = forearm.component
    capsule(c, 110, 21, 18, -19, 38, 'Forearm shell ENVELOPE', white)
    capsule(c, 79, 9, 7, 19.2, 1.5, 'Forearm graphite service panel', black)
    disk(c, 0, 0, -23, 17, 3, 'Elbow output hub', metal)
    disk(c, 110, 0, 20, 22, 16, 'Wrist gearbox ENVELOPE', black)
    disk(c, 110, 0, 36, 20, 3, 'Wrist clean cap', white)
    box(c, (89, 0, -45), (52, 52, 46), 'Wrist motor shroud ENVELOPE', white, 4)
    motor(c, 42, 40, -65, 'NEMA17 wrist provisional', black, metal, 89)

    hand = component(root, '06 | Wrist and parallel gripper concept', wrist, -90)
    c = hand.component
    capsule(c, 30, 17, 15, -15, 30, 'Wrist to gripper bridge', white)
    box(c, (42, 0, 0), (28, 48, 30), 'Servo gripper palm ENVELOPE', black, 3)
    box(c, (42, 0, 16), (22, 30, 2), 'Gripper service lid', white, .7)
    for sign in (-1, 1):
        box(c, (69, sign*19, 0), (38, 8, 14), 'Parallel finger concept', white, 2)
        box(c, (80, sign*14, 0), (16, 3, 12), 'Replaceable grip pad', black, .6)
    box(c, (31, 0, 17.5), (4, 18, 1), 'Amber identification stripe', accent, .3)

    # Four working CAD revolute joints; fixed mounting groups are rigid.
    base.isGrounded = True
    rigid = root.asBuiltJoints.createInput(pedestal, frame, None)
    rigid.setAsRigidJointMotion()
    fixed = root.asBuiltJoints.add(rigid)
    fixed.name = 'Fixed shoulder fork'
    fixed.isLightBulbOn = False
    directions = adsk.fusion.JointDirections
    joint(root, base, pedestal, (0,0,41), 'J1 | Base yaw', directions.ZAxisJointDirection)
    joint(root, frame, upper, shoulder, 'J2 | Shoulder pitch', directions.YAxisJointDirection)
    joint(root, upper, forearm, elbow, 'J3 | Elbow pitch', directions.YAxisJointDirection)
    joint(root, forearm, hand, wrist, 'J4 | Wrist pitch', directions.YAxisJointDirection)
    for occ in root.occurrences:
        occ.component.isOriginFolderLightBulbOn = False
        occ.component.isConstructionFolderLightBulbOn = False
    return root


def run_legacy(context):
    app = adsk.core.Application.get()
    try:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc.name = 'CLEANARM 01 - Concept'
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = build(design)
        cam = app.activeViewport.camera
        cam.isSmoothTransition = False
        cam.eye = pt(440, -620, 360)
        cam.target = pt(50, 0, 100)
        cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
        cam.isFitView = True
        app.activeViewport.camera = cam
        app.activeViewport.fit()
        app.activeViewport.refresh()
        app.activeViewport.saveAsImageFile(os.path.join(OUT, 'CleanArm-01-preview.png'), 1800, 1400)
        export = design.exportManager
        export.execute(export.createFusionArchiveExportOptions(os.path.join(OUT, 'CleanArm-01.f3d')))
        export.execute(export.createSTEPExportOptions(os.path.join(OUT, 'CleanArm-01.step')))
        with open(LOG, 'w') as file:
            json.dump({'status':'success', 'occurrences':root.occurrences.count,
                'joints':root.asBuiltJoints.count, 'warnings':WARNINGS,
                'timeline_issues': [design.timeline.item(i).entity.name
                    for i in range(design.timeline.count)
                    if design.timeline.item(i).entity and hasattr(design.timeline.item(i).entity, 'healthState')
                    and design.timeline.item(i).entity.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState],
                'stage':'Packaging concept; unvalidated mechanics'}, file, indent=2)
    except Exception:
        error = traceback.format_exc()
        with open(LOG, 'w') as file:
            json.dump({'status':'error', 'error':error, 'warnings':WARNINGS}, file, indent=2)
        app.userInterface.messageBox(error)


def run(context):
    # Prepared GreenArm03 entry point; native execution is still pending.
    import importlib.util
    import sys
    for name in ('cad_tools', 'hardware', 'reducer', 'cycloid_math', 'periodic_spline', 'AssemblyAudit', 'FinishAssembly', 'ExportDetails'):
        sys.modules.pop(name, None)
    path = os.path.join(OUT, 'GreenArm-03', 'GreenArm-03.py')
    spec = importlib.util.spec_from_file_location('greenarm03_build', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.run(context)
