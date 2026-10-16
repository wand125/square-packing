import assert from 'node:assert/strict';
import {readFileSync, existsSync, readdirSync} from 'node:fs';
const json=p=>JSON.parse(readFileSync(p,'utf8'));
// JSON serialization normalizes signed zero; the geometry is unchanged.
const source=JSON.parse(JSON.stringify(json('public/data/rect-regions.json')));
const index=json('public/data/rect/index.json');
assert(readFileSync('public/data/rect/index.json').length<10000);
for(const k of source.ks){
 const meta=index.ks.find(x=>x.k===k.k);
 assert.equal(meta.pieceCount,k.pieces.length);
 assert.equal(meta.updated,k.updated);assert.deepEqual(meta.status,k.status);
 assert.equal(meta.ymax,Math.max(...k.pieces.flatMap(p=>p.pts.map(q=>q[0]))));
 assert(!('pieces' in meta));
 assert.deepEqual(json(`public/data/rect/k${k.k}.json`),k);
}
const preview=readFileSync('dist/rect-regions.html','utf8').includes('data-preview="1"');
assert.equal(existsSync('dist/explain.html'),preview);
const built=json('dist/data/rect/index.json');
assert.deepEqual(built.ks,index.ks.filter(k=>preview||k.k<=15));
assert.deepEqual(readdirSync('dist/data/rect').filter(f=>/^k\d+/.test(f)).sort(),built.ks.map(k=>`k${k.k}.json`).sort());
for(const k of built.ks)assert.deepEqual(json(`dist/data/rect/k${k.k}.json`),source.ks.find(x=>x.k===k.k));
assert.deepEqual(json('public/data/papers/triangle-n37.json'),json('dist/data/papers/triangle-n37.json'));
assert.equal(json('public/data/papers/triangle-n37.json').squares.length,37);
assert.deepEqual(json('public/data/papers/triangle-n46.json'),json('dist/data/papers/triangle-n46.json'));
assert.equal(json('public/data/papers/triangle-n46.json').squares.length,46);
console.log(`PASS site data: faithful shards, small index, n37 permanent asset, ${preview?'preview':'release'} filtering.`);
