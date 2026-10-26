#!/usr/bin/env python3
"""Render a world-mm triangle scene with NumPy/Pillow; no GPU or CAD runtime.

Usage: render_cpu.py scene.json preview.png [assembled|front|side] [--internal]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZE = (1500, 1400)
WORK_SIZE = (1800, 1680)
DEFAULT_PALETTE = {
    'green': (0.66, 0.76, 0.69), 'white': (0.93, 0.93, 0.90),
    'graphite': (0.14, 0.17, 0.16), 'metal': (0.49, 0.52, 0.52),
    'black': (0.11, 0.13, 0.12), 'rubber': (0.13, 0.15, 0.14),
}


def unit(value):
    vector = np.asarray(value, dtype=np.float64)
    return vector / max(float(np.linalg.norm(vector)), 1e-12)


def visible_objects(scene, internal=False):
    """Validate all assembled solids; internal view removes only cosmetic covers.

    Hardware stays present in assembled views. Occlusion is determined by the
    depth buffer so any exposed or protruding hardware remains visible.
    """
    result = []
    for obj in scene.get('objects', []):
        role = str(obj.get('role', 'structure')).lower()
        if internal and role == 'cosmetic':
            continue
        vertices = np.asarray(obj.get('vertices', []), dtype=np.float64)
        triangles = np.asarray(obj.get('triangles', []), dtype=np.int64)
        if vertices.size == 0 or triangles.size == 0:
            continue
        if vertices.ndim != 2 or vertices.shape[1] != 3:
            raise ValueError(f"{obj.get('name', 'object')}: vertices must be Nx3")
        if triangles.ndim != 2 or triangles.shape[1] != 3:
            raise ValueError(f"{obj.get('name', 'object')}: triangles must be Nx3")
        if not np.isfinite(vertices).all():
            raise ValueError(f"{obj.get('name', 'object')}: nonfinite vertices")
        if triangles.min() < 0 or triangles.max() >= len(vertices):
            raise ValueError(f"{obj.get('name', 'object')}: triangle index outside vertices")
        result.append({**obj, 'vertices': vertices, 'triangles': triangles})
    if not result:
        raise ValueError('No visible nonempty objects in the scene')
    return result


def camera_for(vertices, mode, width, height):
    directions = {
        'assembled': np.array((505., -800., 235.)),
        'front': np.array((0., -1., .10)),
        'side': np.array((1., 0., .10)),
    }
    toward_eye = unit(directions[mode])
    right = unit(np.cross((0., 0., 1.), toward_eye))
    up = unit(np.cross(toward_eye, right))
    basis = np.vstack((right, up, toward_eye))
    projected = vertices @ basis.T
    low, high = projected[:, :2].min(axis=0), projected[:, :2].max(axis=0)
    span = np.maximum(high - low, 1.)
    scale = min(width * .78 / span[0], height * .77 / span[1])
    center = (high + low) * .5
    offset = np.array((width * .5, height * .49))

    def project(points):
        view = np.asarray(points) @ basis.T
        return np.column_stack(((view[:, 0] - center[0]) * scale + offset[0],
                                -(view[:, 1] - center[1]) * scale + offset[1],
                                view[:, 2]))
    return project, toward_eye


def material_color(obj, palette):
    material = obj.get('material', 'white')
    if isinstance(material, (list, tuple)):
        color = np.asarray(material, dtype=np.float64)
        return np.clip(color / (255 if color.max() > 1 else 1), 0, 1), False
    name = str(material).lower()
    if name in palette:
        color = np.asarray(palette[name], dtype=np.float64)
    else:
        key = next((key for key in ('green', 'white', 'graphite', 'rubber', 'black', 'metal')
                    if key in name), 'white')
        color = np.asarray(palette.get(key, DEFAULT_PALETTE[key]), dtype=np.float64)
    if color.max() > 1:
        color = color / 255
    return np.clip(color, 0, 1), ('green' in name or 'marble' in name)


def background(objects, project, size):
    width, height = size
    yy = np.linspace(0, 1, height)[:, None, None]
    top = np.array((246., 245., 240.))[None, None, :]
    bottom = np.array((229., 230., 222.))[None, None, :]
    canvas = np.repeat(top * (1 - yy) + bottom * yy, width, axis=1)
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    floor_z = min(float(o['vertices'][:, 2].min()) for o in objects) - 1
    for obj in objects:
        points = obj['vertices']
        altitude = np.maximum(points[:, 2] - floor_z, 0)
        floor_points = np.column_stack((points[:, 0] + altitude * .43,
                                         points[:, 1] + altitude * .30,
                                         np.full(len(points), floor_z)))
        screen = project(floor_points)[:, :2]
        for face in obj['triangles']:
            draw.polygon([tuple(x) for x in screen[face]], fill=255)
    blurred = np.asarray(mask.filter(ImageFilter.GaussianBlur(width * .014)), dtype=float) / 255
    return canvas * (1 - .115 * blurred[:, :, None])


def raster_triangle(image, depth, points, world, base_color, marble, toward_eye):
    height, width = depth.shape
    x0 = max(0, int(np.floor(points[:, 0].min())))
    x1 = min(width - 1, int(np.ceil(points[:, 0].max())))
    y0 = max(0, int(np.floor(points[:, 1].min())))
    y1 = min(height - 1, int(np.ceil(points[:, 1].max())))
    if x0 > x1 or y0 > y1:
        return
    a, b, c = points
    denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(denominator) < 1e-9:
        return
    yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
    xx, yy = xx + .5, yy + .5
    u = ((b[1] - c[1]) * (xx - c[0]) + (c[0] - b[0]) * (yy - c[1])) / denominator
    v = ((c[1] - a[1]) * (xx - c[0]) + (a[0] - c[0]) * (yy - c[1])) / denominator
    w = 1 - u - v
    z = u * a[2] + v * b[2] + w * c[2]
    current = depth[y0:y1 + 1, x0:x1 + 1]
    inside = (u >= -1e-8) & (v >= -1e-8) & (w >= -1e-8) & (z > current)
    if not inside.any():
        return
    normal = unit(np.cross(world[1] - world[0], world[2] - world[0]))
    if np.dot(normal, toward_eye) < 0:
        normal = -normal
    key = max(0., float(np.dot(normal, unit((-0.5, -0.7, 1.)))))
    fill = max(0., float(np.dot(normal, unit((0.8, .2, .6)))))
    shade = .65 + .29 * key + .10 * fill
    rgb = np.clip(base_color * 255 * shade, 0, 255)
    region = image[y0:y1 + 1, x0:x1 + 1]
    if marble:
        # Deterministic world-space flecks: roughly 0.35 mm physical grains.
        coordinates = (u[inside, None] * world[0] + v[inside, None] * world[1]
                       + w[inside, None] * world[2])
        cell = np.floor(coordinates / .35)
        grain = np.mod(np.sin(cell @ np.array((127.1, 311.7, 74.7))) * 43758.5453, 1.)
        speckle = np.where(grain < .035, .61, 1.)
        subtle = .989 + grain * .022
        region[inside] = np.clip(rgb[None, :] * (speckle * subtle)[:, None], 0, 255)
    else:
        region[inside] = rgb
    current[inside] = z[inside]


def render(scene, output_path, mode='assembled', internal=False):
    objects = visible_objects(scene, internal)
    vertices = np.vstack([obj['vertices'] for obj in objects])
    width, height = WORK_SIZE
    project, toward_eye = camera_for(vertices, mode, width, height)
    canvas = background(objects, project, (width, height))
    depth = np.full((height, width), -np.inf, dtype=np.float64)
    palette = {**DEFAULT_PALETTE, **scene.get('palette', {})}
    for obj in objects:
        projected = project(obj['vertices'])
        color, marble = material_color(obj, palette)
        for face in obj['triangles']:
            raster_triangle(canvas, depth, projected[face], obj['vertices'][face],
                            color, marble, toward_eye)
    result = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), 'RGB')
    result = result.resize(SIZE, Image.Resampling.LANCZOS)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.save(destination)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('camera', nargs='?', default='assembled',
                        choices=('assembled', 'front', 'side'))
    parser.add_argument('--internal', action='store_true')
    args = parser.parse_args()
    try:
        scene = json.loads(args.input.read_text())
        result = render(scene, args.output, args.camera, args.internal)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'Render failed: {error}\n')
    print(result.resolve())


if __name__ == '__main__':
    main()
