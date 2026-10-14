#!/usr/bin/env python3
"""Independent interval verification on the full ZYZ Euler-angle domain.

No project modules or first-system certificates are imported.  stdout contains
one final JSON record; diagnostics, including unresolved boxes, go to stderr.
"""

import argparse
import json
import math
import sys
import time

from mpmath import iv


DEPTH_LIMIT = 40


def rotation_abs(box):
    """Enclose |Rz(alpha) Ry(beta) Rz(gamma)| entry by entry.

    Box endpoints are exact dyadic coefficients of the *mathematical* pi.
    Multiplication by iv.pi encloses their true angular endpoints, including
    the right endpoints pi and 2*pi.  No ordinary floating-point pi is used.
    """
    alpha, beta, gamma = (iv.mpf(bounds) * iv.pi for bounds in box)
    ca, sa = iv.cos(alpha), iv.sin(alpha)
    cb, sb = iv.cos(beta), iv.sin(beta)
    cg, sg = iv.cos(gamma), iv.sin(gamma)
    return (
        (abs(ca * cb * cg - sa * sg),
         abs(-ca * cb * sg - sa * cg), abs(ca * sb)),
        (abs(sa * cb * cg + ca * sg),
         abs(-sa * cb * sg + ca * cg), abs(sa * sb)),
        (abs(-sb * cg), abs(sb * sg), abs(cb)),
    )


def remaining_columns(box, mask):
    """Remove only columns certified by one of the two strict inequalities."""
    entries = rotation_abs(box)
    half = iv.mpf(1) / 2
    # All interval arithmetic, including squaring and summation, uses iv.
    for k in range(3):
        if mask & (1 << k):
            if any((entries[i][k] ** 2).a > half for i in range(3)):
                mask &= ~(1 << k)
    if not mask:
        return 0
    row_weights = tuple(row[0] + row[1] + row[2] for row in entries)
    for k in range(3):
        if mask & (1 << k):
            terms = tuple(entries[i][k] * (2 - row_weights[i])
                          for i in range(3))
            enclosure = terms[0] + terms[1] + terms[2]
            if enclosure.b < 1:
                mask &= ~(1 << k)
    return mask


def describe_box(box, depth, mask):
    return {
        "depth": depth,
        "open_columns": [k for k in range(3) if mask & (1 << k)],
        "angle_over_pi": box,
        "angle_intervals": [str(iv.mpf(bounds) * iv.pi) for bounds in box],
    }


def check(max_seconds, progress_seconds):
    started = time.monotonic()
    next_progress = started + progress_seconds
    # The common factor pi means these widths order actual angular widths.
    # Binary64 dyadics remain exact through at most 40 midpoint bisections.
    root = ((0.0, 2.0), (0.0, 1.0), (0.0, 2.0))
    stack = [(root, 0, 0b111)]
    boxes = leaves = max_depth = closed_mass = 0
    ok = False
    try:
        while stack:
            now = time.monotonic()
            if now - started >= max_seconds:
                box, depth, mask = stack[-1]
                print("STOP time limit; unresolved box: " +
                      json.dumps(describe_box(box, depth, mask)), file=sys.stderr)
                break
            if now >= next_progress:
                elapsed = now - started
                fraction = closed_mass / (1 << DEPTH_LIMIT)
                print(json.dumps({
                    "progress": True, "boxes": boxes, "leaves": leaves,
                    "seconds": round(elapsed, 3),
                    "boxes_per_second": round(boxes / elapsed, 2),
                    "closed_parameter_fraction": fraction,
                    # A traversal-dependent estimate, never proof evidence.
                    "estimated_total_seconds": (round(elapsed / fraction, 1)
                                                if fraction else None),
                    "pending_boxes": len(stack), "max_depth": max_depth,
                }), file=sys.stderr, flush=True)
                next_progress = now + progress_seconds

            box, depth, mask = stack.pop()
            boxes += 1
            max_depth = max(max_depth, depth)
            mask = remaining_columns(box, mask)
            if not mask:
                leaves += 1
                closed_mass += 1 << (DEPTH_LIMIT - depth)
                continue
            if depth == DEPTH_LIMIT:
                print("FAIL depth limit; unresolved box: " +
                      json.dumps(describe_box(box, depth, mask)), file=sys.stderr)
                break
            axis = max(range(3), key=lambda j: box[j][1] - box[j][0])
            lo, hi = box[axis]
            mid = (lo + hi) / 2
            assert lo < mid < hi
            left, right = list(box), list(box)
            left[axis], right[axis] = (lo, mid), (mid, hi)
            # A parent's closed columns stay certified on both subsets.
            stack.append((tuple(right), depth + 1, mask))
            stack.append((tuple(left), depth + 1, mask))
        else:
            assert closed_mass == 1 << DEPTH_LIMIT
            ok = True
    except KeyboardInterrupt:
        print("STOP interrupted; verification incomplete", file=sys.stderr)
    except Exception as exc:
        print("FAIL checker error: " + repr(exc), file=sys.stderr)

    elapsed = time.monotonic() - started
    print(json.dumps({
        "rate_boxes_per_second": round(boxes / elapsed, 2) if elapsed else 0,
        "closed_parameter_fraction": closed_mass / (1 << DEPTH_LIMIT),
        "complete": ok,
    }), file=sys.stderr)
    result = {"ok": ok, "boxes": boxes, "leaves": leaves,
              "max_depth": max_depth, "seconds": round(elapsed, 6)}
    print(json.dumps(result), flush=True)
    return 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prec", type=int, default=64,
                        help="interval precision in bits, at least 53 (default: 64)")
    parser.add_argument("--max-seconds", type=float, default=1200,
                        help="wall-clock budget (default: 1200 seconds)")
    parser.add_argument("--progress-seconds", type=float, default=30,
                        help="stderr progress interval (default: 30 seconds)")
    args = parser.parse_args()
    if args.prec < 53:
        parser.error("--prec must be at least 53")
    for name in ("max_seconds", "progress_seconds"):
        value = getattr(args, name)
        if not math.isfinite(value) or value <= 0:
            parser.error("--" + name.replace("_", "-") + " must be finite and positive")
    iv.prec = args.prec  # mp.prec alone would NOT set interval precision.
    return check(args.max_seconds, args.progress_seconds)


if __name__ == "__main__":
    sys.exit(main())
