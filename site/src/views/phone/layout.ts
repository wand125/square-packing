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
