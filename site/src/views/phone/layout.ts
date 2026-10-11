/** Move existing bilingual content, preserving nodes and controller event listeners. */
export function layout() {
 const undo: (() => void)[] = [];
 return {
  move(node: Element, parent: Element, before: ChildNode | null = null) {
   const marker = document.createComment('layout'); node.before(marker);
   parent.insertBefore(node, before);
   undo.push(() => { marker.replaceWith(node); });
  },
  add(node: Element, parent: Element) { parent.append(node); undo.push(() => node.remove()); },
  cleanup() { undo.reverse().forEach(fn => fn()); }
 };
}
export const bi = (en: string, ja: string) => `<span data-l="en">${en}</span><span data-l="ja">${ja}</span>`;

/** k small squares in a near-square grid: the icon for "k squares" (a 2 × 2 grid for All). */
export const squaresIcon = (k: number, size = 24) => { const c = Math.ceil(Math.sqrt(k)), r = Math.ceil(k / c), s = 18 / Math.max(c, r);
 return `<svg viewBox="0 0 24 24" width="${size}" height="${size}" aria-hidden="true">` + Array.from({length: k}, (_, i) => `<rect x="${(3 + (i % c) * s + 0.6).toFixed(2)}" y="${(3 + Math.floor(i / c) * s + 0.6).toFixed(2)}" width="${(s - 1.2).toFixed(2)}" height="${(s - 1.2).toFixed(2)}" fill="currentColor" opacity="0.85"/>`).join('') + '</svg>'; };
/** Put the k-squares icon on each k button (data-attr) of a chooser; returns the undo. */
export function iconKButtons(scope: Element, attr: string) {
 const saved: [HTMLElement, string][] = [];
 scope.querySelectorAll<HTMLElement>(`[${attr}]`).forEach(b => { const v = b.getAttribute(attr)!; saved.push([b, b.innerHTML]); b.innerHTML = squaresIcon(v === 'all' ? 4 : +v, 22) + `<span>${b.innerHTML}</span>`; b.classList.add('k-ico'); });
 return () => saved.forEach(([b, h]) => { b.innerHTML = h; b.classList.remove('k-ico'); });
}
