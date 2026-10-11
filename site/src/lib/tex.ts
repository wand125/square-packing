// Typeset the \( … \) parts of a short text (titles, result boxes) at build time.
import katex from 'katex';
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
export const tex = (s: string) => s.split(/(\\\(.*?\\\))/s).map((part) =>
  part.startsWith('\\(') ? katex.renderToString(part.slice(2, -2), { throwOnError: true }) : esc(part)).join('');
