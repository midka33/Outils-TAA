# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals

"""Local polygon pocket repair, independent of Revit (including IronPython 2.7).

Coordinates/limits share the caller's length unit. Rings omit the closing
vertex. A/B are the edges immediately outside a contiguous removed chain.
No nearest-wall lookup and no arbitrary chord fallback are permitted.
"""
import math

MAX_CHAIN_EDGES = 12
MAX_PASSES = 2
MAX_VALIDATIONS = 128
MAX_CONTEXT_SEGMENTS = 2
CONTEXT_EDGE_RATIO = 0.45
CONTEXT_DEPTH_RATIO = 0.50
CONTEXT_MOUTH_RATIO = 0.35
PARALLEL_SIN = 1e-9


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def scale(a, k):
    return (a[0] * k, a[1] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def distance(a, b):
    v = sub(a, b)
    return math.hypot(v[0], v[1])


def signed_area(points):
    if not points:
        return 0.0
    origin = points[0]
    return sum(cross(sub(p, origin), sub(points[(i + 1) % len(points)], origin))
               for i, p in enumerate(points)) * 0.5


def segment_distance(p, a, b):
    v = sub(b, a)
    length2 = dot(v, v)
    if length2 == 0:
        return distance(p, a)
    t = max(0.0, min(1.0, dot(sub(p, a), v) / length2))
    return distance(p, add(a, scale(v, t)))


def on_segment(p, a, b, tol):
    return segment_distance(p, a, b) <= tol


def segment_hits(a, b, c, d, tol):
    """Include touching and collinear overlap, not only proper crossings."""
    if any((on_segment(p, x, y, tol) for p, x, y in
            ((a, c, d), (b, c, d), (c, a, b), (d, a, b)))):
        return True
    ab, cd = sub(b, a), sub(d, c)
    return (cross(ab, sub(c, a)) * cross(ab, sub(d, a)) < 0 and
            cross(cd, sub(a, c)) * cross(cd, sub(b, c)) < 0)


def is_simple(points, tol=1e-7):
    n = len(points)
    if n < 3 or abs(signed_area(points)) <= tol * tol:
        return False
    for i, a in enumerate(points):
        b, prev = points[(i + 1) % n], points[(i - 1) % n]
        if distance(a, b) <= tol:
            return False
        # Adjacent reversal/overlap is invalid too.
        if on_segment(b, prev, a, tol) or on_segment(prev, a, b, tol):
            return False
        for j in range(i + 1, n):
            if j == i + 1 or (i == 0 and j == n - 1):
                continue
            if segment_hits(a, b, points[j], points[(j + 1) % n], tol):
                return False
    return True


def inside(p, ring, tol=1e-7):
    result = False
    for i, a in enumerate(ring):
        b = ring[(i + 1) % len(ring)]
        if on_segment(p, a, b, tol):
            return True
        if (a[1] > p[1]) != (b[1] > p[1]):
            if p[0] < a[0] + (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]):
                result = not result
    return result


def contains_ring(outer, inner, tol=1e-7):
    """Check entire edges, splitting at every boundary intersection.

    Vertex-only or area-only checks miss cuts through a concave ring.
    Shared/collinear boundary edges are accepted.
    """
    if not all(inside(p, outer, tol) for p in inner):
        return False
    for i, a in enumerate(inner):
        b = inner[(i + 1) % len(inner)]
        v = sub(b, a)
        vv = dot(v, v)
        if vv <= tol * tol:
            return False
        cuts = [0.0, 1.0]
        for j, c in enumerate(outer):
            d = outer[(j + 1) % len(outer)]
            w = sub(d, c)
            denominator = cross(v, w)
            if abs(denominator) > PARALLEL_SIN * math.sqrt(vv * dot(w, w)):
                t = cross(sub(c, a), w) / denominator
                u = cross(sub(c, a), v) / denominator
                if 0 <= t <= 1 and 0 <= u <= 1:
                    cuts.append(t)
            else:
                for p in (c, d):
                    if on_segment(p, a, b, tol):
                        cuts.append(max(0.0, min(1.0, dot(sub(p, a), v) / vv)))
        cuts.sort()
        for t0, t1 in zip(cuts, cuts[1:]):
            if not inside(add(a, scale(v, (t0 + t1) * 0.5)), outer, tol):
                return False
    return True


def simplify(points, tol):
    """Remove exact collinear subdivisions only; never flatten a small kink."""
    result = list(points)
    changed = True
    while changed and len(result) > 3:
        changed = False
        for i, p in enumerate(result):
            a, b = result[i - 1], result[(i + 1) % len(result)]
            v, w = sub(p, a), sub(b, p)
            if (abs(cross(v, w)) <= PARALLEL_SIN * distance(p, a) * distance(b, p)
                    and dot(v, w) > 0):
                result.pop(i)
                changed = True
                break
    return result


def _cyclic(points, index):
    return points[index % len(points)]


def context_edge_is_parasitic(edge_length, outer_length, pocket_length,
                              max_mouth, max_depth, tol=1e-7):
    """Return True only for a short local support edge worth absorbing.

    The decision is deliberately relative to its local context. This avoids
    turning the pocket cleaner into a global polygon simplifier.
    """
    if min(edge_length, outer_length) <= tol:
        return False
    local_limit = min(
        max_depth * CONTEXT_DEPTH_RATIO,
        max_mouth * CONTEXT_MOUTH_RATIO,
    )
    reference = max(outer_length, pocket_length)
    return (
        edge_length <= local_limit + tol
        and edge_length <= reference * CONTEXT_EDGE_RATIO + tol
    )


def support_context(points, start, end):
    """Return the local A / pocket / B context for cyclic offsets."""
    n = len(points)
    return dict(
        previous=_cyclic(points, start - 1),
        a=_cyclic(points, start),
        b=_cyclic(points, end),
        following=_cyclic(points, end + 1),
        interior=[_cyclic(points, i) for i in range(start + 1, end)],
        outside=[_cyclic(points, i) for i in range(end + 1, start + n)],
        start=start,
        end=end,
        chain_edges=end - start,
    )


def normalize_support_context(points, steps, max_mouth, max_depth,
                              tolerance=1e-7,
                              max_context_segments=MAX_CONTEXT_SEGMENTS):
    """Absorb at most two short support edges around an already local pocket.

    The initial pocket remains the source of truth. Only the immediately
    adjacent support edge can be absorbed, then at most one more on the same
    side. This is bounded local context, not a search across arbitrary pairs.
    """
    n = len(points)
    start, end = 0, steps
    left_absorbed = 0
    right_absorbed = 0

    for _unused in range(max_context_segments):
        if end - (start - 1) > n - 3:
            break
        edge_length = distance(
            _cyclic(points, start - 1),
            _cyclic(points, start),
        )
        outer_length = distance(
            _cyclic(points, start - 2),
            _cyclic(points, start - 1),
        )
        pocket_length = distance(
            _cyclic(points, start),
            _cyclic(points, start + 1),
        )
        if not context_edge_is_parasitic(
            edge_length, outer_length, pocket_length,
            max_mouth, max_depth, tolerance,
        ):
            break
        start -= 1
        left_absorbed += 1

    for _unused in range(max_context_segments):
        if (end + 1) - start > n - 3:
            break
        edge_length = distance(
            _cyclic(points, end),
            _cyclic(points, end + 1),
        )
        outer_length = distance(
            _cyclic(points, end + 1),
            _cyclic(points, end + 2),
        )
        pocket_length = distance(
            _cyclic(points, end - 1),
            _cyclic(points, end),
        )
        if not context_edge_is_parasitic(
            edge_length, outer_length, pocket_length,
            max_mouth, max_depth, tolerance,
        ):
            break
        end += 1
        right_absorbed += 1

    context = support_context(points, start, end)
    context["left_absorbed"] = left_absorbed
    context["right_absorbed"] = right_absorbed
    context["absorbed"] = left_absorbed + right_absorbed
    return context


def support_paths(previous, a, b, following, max_extension, tol=1e-7):
    """At most two replacements, defined solely by supporting edges A/B."""
    va, vb = sub(a, previous), sub(following, b)
    la, lb = distance(a, previous), distance(following, b)
    if min(la, lb) <= tol:
        return []
    u, v = scale(va, 1.0 / la), scale(vb, 1.0 / lb)
    denominator = cross(u, v)
    if abs(denominator) > PARALLEL_SIN:
        intersection = add(a, scale(u, cross(sub(b, a), v) / denominator))
        if max(distance(intersection, a), distance(intersection, b)) > max_extension:
            return []
        # TR may shorten A/B, but must not reverse either supporting edge.
        if dot(sub(intersection, previous), u) <= tol or dot(sub(following, intersection), v) <= tol:
            return []
        return [("trim", [intersection])]
    if dot(u, v) <= 0:
        return []  # Opposite traversal would fold back onto the same support.
    separation = abs(cross(sub(b, a), u))
    if separation <= 1e-9:
        if dot(sub(b, a), u) <= tol:
            return []
        return [("collinear", [a, b])]
    # Orthogonal projection in each direction. Both candidates preserve A/B.
    projected_b = add(b, scale(v, dot(sub(a, b), v)))
    projected_a = add(a, scale(u, dot(sub(b, a), u)))
    paths = []
    for path in ([a, projected_b], [projected_a, b]):
        if max(distance(path[0], a), distance(path[-1], b)) > max_extension:
            continue
        if dot(sub(path[0], previous), u) <= tol or dot(sub(following, path[-1]), v) <= tol:
            continue
        paths.append(("perpendicular", path))
    return paths


def valid_replacement(original, candidate, max_area, tol=1e-7):
    area, candidate_area = signed_area(original), signed_area(candidate)
    added = abs(candidate_area) - abs(area)
    if area * candidate_area <= 0 or added <= tol * tol or added > max_area + tol * tol:
        return False
    return is_simple(candidate, tol) and contains_ring(candidate, original, tol)


def empty_diagnostics():
    return dict(collinear=0, trim=0, perpendicular=0, absorbed=0,
                candidates=0, validations=0, budget_exhausted=False)


def close_pockets(points, max_mouth, max_depth, max_area, max_extension,
                  tolerance=1e-7, max_chain_edges=MAX_CHAIN_EDGES,
                  max_passes=MAX_PASSES, max_validations=MAX_VALIDATIONS):
    """Bounded local scans with local A/B normalization.

    A detected pocket can absorb at most two short support edges on each side
    before the existing collinear / Trim-Extend / perpendicular rules run.
    This removes the small residual steps seen next to technical shafts without
    introducing a global simplification pass.
    """
    ring = list(points)
    stats = empty_diagnostics()
    if not is_simple(ring, tolerance):
        return ring, stats
    ring = simplify(ring, tolerance)

    for _pass in range(max_passes):
        changed = False
        i = 0
        visited = 0
        sweep_limit = len(ring)

        while i < len(ring) and visited < sweep_limit:
            visited += 1
            n = len(ring)
            rotated = ring[i:] + ring[:i]
            sign = 1 if signed_area(rotated) > 0 else -1
            best = None
            has_concavity = False

            for steps in range(2, min(max_chain_edges, n - 3) + 1):
                p, q, r = rotated[steps - 2:steps + 1]
                has_concavity |= (
                    cross(sub(q, p), sub(r, q)) * sign
                    < -tolerance * tolerance
                )
                if not has_concavity:
                    continue

                base = support_context(rotated, 0, steps)
                base["left_absorbed"] = 0
                base["right_absorbed"] = 0
                base["absorbed"] = 0

                normalized = normalize_support_context(
                    rotated,
                    steps,
                    max_mouth,
                    max_depth,
                    tolerance,
                )

                contexts = [base]
                if normalized["absorbed"]:
                    contexts.insert(0, normalized)

                seen_contexts = set()

                for context in contexts:
                    key = (context["start"], context["end"])
                    if key in seen_contexts:
                        continue
                    seen_contexts.add(key)

                    previous = context["previous"]
                    a = context["a"]
                    b = context["b"]
                    following = context["following"]
                    interior = context["interior"]
                    outside = context["outside"]

                    if not interior:
                        continue

                    # Normalized A/B must themselves be real outward lips.
                    if (
                        cross(
                            sub(a, previous),
                            sub(interior[0], a),
                        ) * sign <= 0
                        or cross(
                            sub(b, interior[-1]),
                            sub(following, b),
                        ) * sign <= 0
                    ):
                        continue

                    if distance(a, b) > max_mouth:
                        continue

                    if any(
                        distance(point, a) > max_mouth + 2 * max_depth
                        for point in interior
                    ):
                        continue

                    stats["candidates"] += 1

                    options = support_paths(
                        previous,
                        a,
                        b,
                        following,
                        max_extension,
                        tolerance,
                    )

                    for kind, path in options:
                        bridge = [a] + path + [b]
                        if any(
                            min(
                                segment_distance(point, x, y)
                                for x, y in zip(bridge, bridge[1:])
                            ) > max_depth
                            for point in interior
                        ):
                            continue

                        candidate = simplify(
                            path + outside,
                            tolerance,
                        )
                        original = [
                            _cyclic(rotated, offset)
                            for offset in range(
                                context["start"],
                                context["start"] + n,
                            )
                        ]
                        added = (
                            abs(signed_area(candidate))
                            - abs(signed_area(original))
                        )

                        if (
                            added <= tolerance * tolerance
                            or added > max_area
                        ):
                            continue

                        if stats["validations"] >= max_validations:
                            stats["budget_exhausted"] = True
                            return ring, stats

                        stats["validations"] += 1

                        if valid_replacement(
                            original,
                            candidate,
                            max_area,
                            tolerance,
                        ):
                            # A short adjacent support edge is absorbed only
                            # after all the same safety checks as the original
                            # pocket. Prefer this normalized solution, then the
                            # longest local chain, then least added area.
                            score = (
                                -context["absorbed"],
                                -context["chain_edges"],
                                added,
                            )
                            if best is None or score < best[0]:
                                best = (
                                    score,
                                    candidate,
                                    kind,
                                    context["absorbed"],
                                )

            if best is not None:
                ring = best[1]
                stats[best[2]] += 1
                stats["absorbed"] += best[3]
                changed = True
                i = 1
            else:
                i += 1

        if not changed:
            return ring, stats

    stats["budget_exhausted"] = True
    return ring, stats
