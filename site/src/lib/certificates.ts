import {readFileSync} from 'node:fs';
interface Entry {file: string; n: number; kind: 'point'|'lift'|'rect'|'mixed'; v: number; best?: boolean}
export const certificates: Entry[] = JSON.parse(readFileSync('public/data/certs/index.json', 'utf8'));
export const best = certificates.filter(c=>c.best !== false);
export const first = best.find(c=>c.n===41) || best[0];
export const name = (c: Entry) => 'certs/'+c.file.slice(0,-5);
export const value = (c: Entry) => c.v.toFixed(6).replace(/0+$/,'').replace(/\.$/,'');
export const versions: Record<number, [string,string,string,boolean][]> = {};
for(const c of [...certificates].sort((a,b)=>a.n-b.n || b.v-a.v || (a.file<b.file?-1:a.file>b.file?1:0))) {
 (versions[c.n] ||= []).push([name(c),value(c),c.kind,c.best!==false]);
}
export const kinds = {point:'points',lift:'points + segments',rect:'rectangles',mixed:'mixed'};
export const icons = {
 point:'<circle cx="3.5" cy="4" r="1.6"/><circle cx="10" cy="3.5" r="1.6"/><circle cx="6.5" cy="10" r="1.6"/><circle cx="11.5" cy="10.5" r="1.2"/>',
 lift:'<path d="M1 7H13" stroke="currentColor" stroke-width="1.4" fill="none"/><circle cx="3.5" cy="3" r="1.4"/><circle cx="10.5" cy="11" r="1.4"/>',
 rect:'<rect x="2" y="3" width="10" height="8" rx="0.5" fill="currentColor" opacity="0.55"/>',
 mixed:'<rect x="1.5" y="2" width="6.5" height="5" fill="currentColor" opacity="0.55"/><rect x="5" y="7" width="7.5" height="5" fill="currentColor" opacity="0.8"/>'
};
