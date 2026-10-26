"""Uniform cubic periodic interpolation without CAD sketch constraints.

For n samples q_i, solve P_(i-1) + 4 P_i + P_(i+1) = 6 q_i cyclically.
Jacobi iteration is a strict infinity-norm contraction with factor <= 1/2.
Returned controls start at P_(n-1), P_0, P_1, ... P_(n-2), then repeat the
first three. Thus degree=3, knots=0..n+6, domain=[3,n+3], and the curve at
u=3+i interpolates q_i WITHOUT a one-sample phase shift. Weights are all 1.

Use the returned controls/knots to create a non-rational cubic NURBS directly;
the repeated controls make position, tangent and second derivative periodic.
No fit-point constraints or SketchFittedSpline.isClosed solving is needed.
"""
import math


def periodic_controls(points, tolerance=1e-12, max_iterations=128):
    """Return n+3 immutable control-point tuples; input omits closing duplicate."""
    try:
        samples = tuple(tuple(float(value) for value in point) for point in points)
    except (TypeError, ValueError) as exc:
        raise ValueError('Points must contain finite coordinate sequences.') from exc
    if len(samples) < 4:
        raise ValueError('At least four periodic samples are required.')
    dimension = len(samples[0])
    if dimension < 2 or any(len(p) != dimension for p in samples):
        raise ValueError('All points must have the same dimension, at least two.')
    if not all(math.isfinite(value) for point in samples for value in point):
        raise ValueError('Point coordinates must be finite.')
    if samples[0] == samples[-1]:
        raise ValueError('Omit the duplicate closing sample.')
    if not math.isfinite(tolerance) or tolerance <= 0 or max_iterations < 1:
        raise ValueError('Tolerance and iteration limit must be positive.')
    controls = samples
    n = len(samples)
    for _ in range(max_iterations):
        updated = tuple(tuple(1.5 * samples[i][axis] - .25 * (
            controls[(i-1) % n][axis] + controls[(i+1) % n][axis])
            for axis in range(dimension)) for i in range(n))
        delta = max(abs(a-b) for p, q in zip(updated, controls) for a, b in zip(p, q))
        controls = updated
        if delta <= tolerance:
            # This rotation makes knot u=3 align with sample zero.
            rotated = controls[-1:] + controls[:-1]
            return rotated + rotated[:3]
    raise ValueError('Periodic interpolation did not converge to requested tolerance.')


def uniform_knots(controls):
    """Full simple uniform knot vector, length len(controls)+degree+1."""
    if len(controls) < 7:
        raise ValueError('Need n+3 controls for n>=4 periodic samples.')
    return tuple(float(i) for i in range(len(controls) + 4))


def evaluate_periodic(controls, u, derivative=0):
    """Evaluate cubic curve or first/second derivative in knot-coordinate units."""
    if derivative not in (0, 1, 2) or not math.isfinite(u):
        raise ValueError('Require finite parameter and derivative in {0,1,2}.')
    n = len(controls) - 3
    if n < 4:
        raise ValueError('Need n+3 controls for n>=4 periodic samples.')
    wrapped = (u - 3) % n
    segment = math.floor(wrapped)
    t = wrapped - segment
    if derivative == 0:
        basis = ((1-t)**3/6, (3*t**3-6*t*t+4)/6,
                 (-3*t**3+3*t*t+3*t+1)/6, t**3/6)
    elif derivative == 1:
        basis = (-.5*(1-t)**2, 1.5*t*t-2*t, -1.5*t*t+t+.5, .5*t*t)
    else:
        basis = (1-t, 3*t-2, 1-3*t, t)
    return tuple(sum(basis[j] * controls[segment+j][axis] for j in range(4))
                 for axis in range(len(controls[0])))
