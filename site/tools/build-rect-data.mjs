// Generate local shards from the extraction output. No source tree is modified.
import {readFile, mkdir, writeFile, realpath, readdir, rm} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve, sep} from 'node:path';
export async function buildRectData() {
 const root=fileURLToPath(new URL('../',import.meta.url));
 const data=await realpath(resolve(root,'public/data'));
 if(!data.startsWith(root.endsWith(sep)?root:root+sep))throw new Error('public/data must be local');
 const source=JSON.parse(await readFile(resolve(data,'rect-regions.json'),'utf8'));
 const dir=resolve(data,'rect'); await mkdir(dir,{recursive:true});
 const ks=[];
 for(const edge of source.ks){
  const {pieces,...meta}=edge;
  ks.push({...meta,pieceCount:pieces.length,ymax:Math.max(...pieces.flatMap(p=>p.pts.map(q=>q[0])))});
  await writeFile(resolve(dir,`k${edge.k}.json`),JSON.stringify(edge)+'\n');
 }
 for(const file of await readdir(dir))if(/^k\d+\.json$/.test(file)&&!ks.some(k=>file===`k${k.k}.json`))await rm(resolve(dir,file));
 await writeFile(resolve(dir,'index.json'),JSON.stringify({...source,ks})+'\n');
 console.log(`Wrote rect/index.json and ${ks.length} k shards`);
}
if(process.argv[1]===fileURLToPath(import.meta.url))await buildRectData();
