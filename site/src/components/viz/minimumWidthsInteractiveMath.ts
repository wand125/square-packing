/** Display arithmetic for the paper illustration; not a packing or proof checker. */
export const UI_MIN_N = 11;
export const UI_MAX_N = 60;
export const UI_MIN_A = 1851;
export const UI_MAX_A = 1999;

type Point = [number, number];
export type DrawingSquare = { vertices: Point[]; cap: boolean };

function branch(n: number, a: number, t: number) {
  const den = 1 + t * t;
  const c = (1 - t * t) / den, s = 2 * t / den, h = c + s;
  const b = 1.5 * a - 1, q = h * h - 1;
  const P = (2 * h - a) / q, Q = 1 + (2 * h - b) / q;
  const A = (2 - a) * (s / c - c / s) / 4;
  const ht = 2 * (1 - 2 * t - t * t) / (den * den);
  const Ph = -2 * (h * h - a * h + 1) / (q * q);
  const Qh = -2 * (h * h - b * h + 1) / (q * q);
  const At = (2 - a) / (2 * den * c * c * s * s);
  return { c, s, h, width: (n - 4) * P + 2 * Q - 2 * A,
    derivative: ((n - 4) * Ph + 2 * Qh) * ht - 2 * At };
}

export function packingDrawing(n: number, milliHeight: number) {
  if (!Number.isInteger(n) || n < UI_MIN_N || n > UI_MAX_N ||
      !Number.isInteger(milliHeight) || milliHeight < UI_MIN_A || milliHeight > UI_MAX_A) {
    throw new Error('Outside the illustration controls');
  }
  const a = milliHeight / 1000, odd = n % 2 === 1;
  let c: number, s: number, h: number, width: number, angle: number;
  if (odd) {
    c = s = Math.SQRT1_2; h = Math.SQRT2;
    width = 4 + 2 * (n - 2) * Math.SQRT2 - (n - 1) * a;
    angle = 45;
  } else {
    let lo = Math.SQRT2 - 1, hi = 43 / 100;
    const dl = branch(n, a, lo).derivative, dh = branch(n, a, hi).derivative;
    if (!Number.isFinite(dl) || !Number.isFinite(dh) || !(dl < 0 && dh > 0)) {
      throw new Error('Cannot bracket the drawing angle');
    }
    for (let i = 0; i < 48; i++) {
      const mid = (lo + hi) / 2;
      if (mid === lo || mid === hi) break;
      const derivative = branch(n, a, mid).derivative;
      if (!Number.isFinite(derivative)) throw new Error('Nonfinite drawing angle');
      if (derivative > 0) hi = mid; else lo = mid;
    }
    const t = (lo + hi) / 2, v = branch(n, a, t);
    ({ c, s, h, width } = v); angle = 2 * Math.atan(t) * 180 / Math.PI;
  }
  if (![c, s, h, width, angle].every(Number.isFinite)) throw new Error('Nonfinite drawing');
  const gap = a - h, fPlus = (1 - s * gap) / c, fMinus = (1 - c * gap) / s;
  const capH = (1 + h) / 2;
  const capPlus = (capH - s * (a - capH)) / c;
  const capMinus = (capH - c * (a - capH)) / s;
  const squares: DrawingSquare[] = [];
  function square(x: number, y: number, cap: boolean) {
    const co = cap ? 1 : c, si = cap ? 0 : s;
    const corners: Point[] = [[-.5, -.5], [.5, -.5], [.5, .5], [-.5, .5]];
    squares.push({ cap, vertices: corners.map<Point>(([u, v]) => [x + u * co - v * si, y + u * si + v * co]) });
  }
  square(.5, a - .5, true);
  const interior = n - 2;
  let x = .5 + capMinus;
  for (let j = 0; j < interior; j++) {
    const lower = j % 2 === 0;
    square(x, lower ? h / 2 : a - h / 2, false);
    if (j + 1 < interior) x += lower ? fPlus : fMinus;
  }
  const lastLower = (interior - 1) % 2 === 0;
  const capX = x + (lastLower ? capPlus : capMinus);
  square(capX, lastLower ? a - .5 : .5, true);
  if (Math.abs(capX + .5 - width) > 1e-10 * Math.max(1, width)) {
    throw new Error('Inconsistent drawing width');
  }
  return { n, a, odd, width, angle, squares };
}
