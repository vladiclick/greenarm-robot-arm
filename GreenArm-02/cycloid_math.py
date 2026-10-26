"""Sampled 12-roller/11-lobe cycloidal geometry, in millimetres and radians.

The profile is the inward normal offset of the fixed-roller centre envelope
q(t) = R*exp(i*t) - e*exp(i*N*t). This is the conventional one-tooth-difference
external pin-ring cycloid. Input alpha gives eccentric-centre angle alpha and
disc angle -alpha/(N-1). No CAD API or non-standard dependency is required.

Clearance is a NORMAL profile offset, not a tooth-scale factor. Polygonal CAD
construction adds sampling error; use >=1440 samples for these dimensions.
Numerical interference checks do not establish load capacity, durability,
print tolerance, friction, efficiency, backlash or a guaranteed smooth motion.
"""
import math


def _validate(R, r, e, N, samples=720, clearance=.1):
    values = (R, r, e, clearance)
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
        raise ValueError('Dimensions must be finite numbers.')
    if not isinstance(N, int) or N < 3:
        raise ValueError('N must be an integer of at least three ring rollers.')
    if min(R, r, e) <= 0 or clearance < 0:
        raise ValueError('Radii and eccentricity must be positive; clearance nonnegative.')
    if N * e >= R:
        raise ValueError('This implementation requires N*e < R to avoid envelope cusps.')
    if r + clearance >= R - e:
        raise ValueError('Roller/clearance consumes the profile radius.')
    if 2 * (r + clearance) >= 2 * R * math.sin(math.pi / N):
        raise ValueError('Adjacent fixed rollers overlap.')
    if not isinstance(samples, int) or samples < N * 16:
        raise ValueError('Use at least 16 samples per ring roller.')


def _rotate(point, angle):
    x, y = point
    c, s = math.cos(angle), math.sin(angle)
    return (c * x - s * y, s * x + c * y)


def profile_point(t, R=40, r=5, e=1.5, N=12, clearance=.1):
    """One point in the disc's own frame (disc centre is origin)."""
    a, b = complex(math.cos(t), math.sin(t)), complex(math.cos(N*t), math.sin(N*t))
    centre_curve = R * a - e * b
    outward_normal = R * a - N * e * b
    if abs(outward_normal) == 0:
        raise ValueError('Singular profile normal.')
    point = centre_curve - (r + clearance) * outward_normal / abs(outward_normal)
    return (point.real, point.imag)


def cycloid_points(R, r, e, N, samples=720, input_angle=0, phase=0, clearance=.1):
    """Return open tuple of perimeter vertices in GLOBAL assembled coordinates.

    `phase` is the eccentric phase: 0 for disc A; pi for disc B. Each identical
    local outer profile gets canonical orientation -(input_angle+phase)/(N-1).
    With 12 rollers / 11 lobes a physical 180-degree second-disc rotation is
    equivalent by the outer profile's 11-fold rotational symmetry.
    """
    _validate(R, r, e, N, samples, clearance)
    if not all(math.isfinite(v) for v in (input_angle, phase)):
        raise ValueError('Angles must be finite.')
    alpha = input_angle + phase
    centre = (e * math.cos(alpha), e * math.sin(alpha))
    orientation = -alpha / (N - 1)
    local = (profile_point(2 * math.pi * k / samples, R, r, e, N, clearance)
             for k in range(samples))
    rotated = (_rotate(p, orientation) for p in local)
    return tuple((p[0] + centre[0], p[1] + centre[1]) for p in rotated)


def assembly_disc_geometry(R=40, r=5, e=1.5, N=12, samples=1440,
                           input_angle=0, disc_phase=0, clearance=.1,
                           output_radius=22, output_count=6,
                           output_pin_radius=2, output_clearance=.15,
                           bearing_bore_radius=10.6):
    """Independent disc geometry plus common output-carrier pin centres.

    Disc B's local hole pattern has angular phase +pi/(N-1). This compensates
    its -pi/(N-1) profile phase so both discs engage the SAME carrier pins.
    For this 11-lobe / 6-hole geometry, an IDENTICAL first disc rotated 180 deg
    gives the same assembled geometry (11-fold profile and 6-fold hole symmetry).
    The canonical local hole pattern here is a coordinate choice, not a demand
    to manufacture two different parts. Use global geometry for direct CAD.
    Hole centres in the assembly are eccentric from the output pins by e.
    `bearing_bore_radius=10.6` is a proposed 0.1 mm radial fit allowance around
    a 6801 bearing (12x21x5); calibrate this fit on the actual printer.
    """
    profile_global = cycloid_points(R, r, e, N, samples, input_angle, disc_phase, clearance)
    if output_count < 3 or output_radius <= 0 or output_pin_radius <= 0 or output_clearance < 0:
        raise ValueError('Invalid output pin pattern.')
    alpha = input_angle + disc_phase
    centre = (e * math.cos(alpha), e * math.sin(alpha))
    orientation = -alpha / (N - 1)
    output_angle = -input_angle / (N - 1)
    hole_phase = disc_phase / (N - 1)
    hole_angles = tuple(2 * math.pi * k / output_count for k in range(output_count))
    holes_local = tuple((output_radius * math.cos(a + hole_phase),
                         output_radius * math.sin(a + hole_phase)) for a in hole_angles)
    holes_rotated = tuple(_rotate(p, orientation) for p in holes_local)
    holes_global = tuple((p[0] + centre[0], p[1] + centre[1]) for p in holes_rotated)
    pins = tuple((output_radius * math.cos(a + output_angle),
                  output_radius * math.sin(a + output_angle)) for a in hole_angles)
    return dict(
        reduction_ratio=N-1, eccentric_center=centre,
        profile_orientation=orientation, output_angle=output_angle,
        local_hole_phase=hole_phase,
        profile_local=tuple(profile_point(2 * math.pi * k / samples, R, r, e, N, clearance)
                            for k in range(samples)),
        profile_global=profile_global,
        output_holes_local=holes_local, output_holes_global=holes_global,
        output_pins_global=pins,
        output_hole_radius=e + output_pin_radius + output_clearance,
        bearing_bore_radius=bearing_bore_radius,
    )


def _point_segment_distance(point, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    denominator = dx * dx + dy * dy
    if denominator == 0:
        return math.dist(point, a)
    t = max(0, min(1, ((point[0]-a[0])*dx + (point[1]-a[1])*dy) / denominator))
    return math.dist(point, (a[0] + t*dx, a[1] + t*dy))


def _point_inside(point, polygon):
    x, y = point
    crossings = (
        (a[1] > y) != (b[1] > y) and
        x < (b[0]-a[0]) * (y-a[1]) / (b[1]-a[1]) + a[0]
        for a, b in zip(polygon, polygon[1:] + polygon[:1])
    )
    return sum(crossings) % 2 == 1


def minimum_roller_clearance(points, R=40, r=5, N=12):
    """Signed minimum clearance between sampled polygon and fixed roller ring."""
    polygon = tuple(points)
    edges = tuple(zip(polygon, polygon[1:] + polygon[:1]))
    centres = tuple((R*math.cos(2*math.pi*k/N), R*math.sin(2*math.pi*k/N)) for k in range(N))
    distances = tuple(min(_point_segment_distance(c, a, b) for a, b in edges) for c in centres)
    return min((-d if _point_inside(c, polygon) else d) - r for c, d in zip(centres, distances))


def validate_design(**kwargs):
    """Conservative LOCAL material-web and pin/hole geometry checks."""
    geometry = assembly_disc_geometry(**kwargs)
    holes = geometry['output_holes_local']
    hole_r = geometry['output_hole_radius']
    bearing_web = min(math.hypot(*p) - hole_r - geometry['bearing_bore_radius'] for p in holes)
    inner_profile_radius = min(math.hypot(*p) for p in geometry['profile_local'])
    rim_web = inner_profile_radius - max(math.hypot(*p) + hole_r for p in holes)
    adjacent_web = min(math.dist(a, b) - 2*hole_r for i, a in enumerate(holes) for b in holes[i+1:])
    roller_gap = minimum_roller_clearance(geometry['profile_global'],
                                         kwargs.get('R', 40), kwargs.get('r', 5), kwargs.get('N', 12))
    return dict(valid=min(bearing_web, rim_web, adjacent_web, roller_gap) > 0,
                minimum_bearing_web=bearing_web, conservative_rim_web=rim_web,
                adjacent_output_hole_web=adjacent_web, minimum_roller_clearance=roller_gap)


if __name__ == '__main__':
    import json
    print(json.dumps(validate_design(), indent=2))
