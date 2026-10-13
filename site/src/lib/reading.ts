import type { Bi, Source } from './data';
import { GH, PAGES, url , PREVIEW} from './sitemap';
export const BLOB = GH + '/blob/main/';
export const esc = (v: unknown = '') => String(v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#x27;');
export const code = (v: string) => esc(v).replace(/`([^`]+)`/g, '<code>$1</code>');
export function bi(en: string, ja = en): string { return !ja || ja === en ? esc(en) : `<span data-l="en">${esc(en)}</span><span data-l="ja">${esc(ja)}</span>`; }
export function bd(d?: Bi): string { return !d ? '' : typeof d === 'string' ? esc(d) : bi(d.en || '', d.ja || d.en || ''); }
export function bc(d?: Bi): string { if (!d) return ''; if (typeof d === 'string') return code(d); const en = d.en || '', ja = d.ja || en; return en === ja ? code(en) : `<span data-l="en">${code(en)}</span><span data-l="ja">${code(ja)}</span>`; }
export const a = (href: string, text: string) => `<a href="${esc(href)}">${text}</a>`;
export function sourceLinks(s?: Source): string {
  if (!s) return '';
  return (Array.isArray(s) ? s : s.split(/;\s*/)).flatMap(item => { const parts = item.split(/,\s*(?=L\d)/); return [parts[0], ...parts.slice(1).map(p => parts[0].split('#')[0] + '#' + p)]; }).map(item => {
    const it = item.trim(); if (!it) return '';
    if (it.startsWith('http')) return a(it, esc(it.split('github.com/').at(-1)));
    const path = it.split(' ')[0], bits = path.split('#')[0].split('/');
    return a(BLOB + path, esc(bits.length >= 3 ? bits.slice(-2).join('/') : bits.join('/')));
  }).join('');
}
export const PAPER_BY_ISSUE: Record<number, string> = {1: 'paper-closed-form.html', 15: 'paper-hexagon-n3.html', 16: 'paper-domino.html', 17: 'paper-triangle.html', 4: 'paper-triangle.html', 13: 'paper-right-isosceles.html', 14: 'paper-valid7.html'};
export function paperLink(issue: number, title: string) { const file = PAPER_BY_ISSUE[issue]; return file && PAGES.some(p => p.file === file && (PREVIEW || !p.preview)) ? a(url(file), title) : title; }
export const cell = (html: string, cls = '') => `<td${cls ? ` class="${cls}"` : ''}>${html}</td>`;
export const row = (cells: string[]) => `<tr>${cells.join('')}</tr>`;
export const term = (label: string, value: string) => `<dt>${label}</dt><dd>${value}</dd>`;
