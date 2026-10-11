import {readFile, writeFile, readdir, rm, lstat} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {join} from 'node:path';
import {buildRectData} from '../tools/build-rect-data.mjs';

/** Filter only the materialized build output; source extraction remains intact. */
export function interactiveData() {
 return {name:'interactive-data',hooks:{'astro:build:start':buildRectData,'astro:build:done':async ({dir})=>{
  const target=join(fileURLToPath(dir),'data');
  if((await lstat(target)).isSymbolicLink()) throw new Error('Build data must be a copy, never a source symlink');
  if(process.env.SP_PREVIEW==='1') return;
  await rm(join(fileURLToPath(dir),'explain.html'),{force:true});
  const rect=join(target,'rect');
  const ri=JSON.parse(await readFile(join(rect,'index.json'),'utf8'));
  ri.ks=ri.ks.filter(k=>k.k<=15);
  await writeFile(join(rect,'index.json'),JSON.stringify(ri));
  for(const file of await readdir(rect))if(/^k(\d+)\.json$/.test(file)&&+file.match(/^k(\d+)/)[1]>15)await rm(join(rect,file));
  const file=join(target,'rect-regions.json');
  const data=JSON.parse(await readFile(file,'utf8'));
  data.ks=data.ks.filter(k=>k.k<=15);
  await writeFile(file,JSON.stringify(data));
  const music=join(target,'music');
  const index=JSON.parse(await readFile(join(music,'index.json'),'utf8'));
  for(const k of Object.keys(index))if(+k>=16)delete index[k];
  await writeFile(join(music,'index.json'),JSON.stringify(index));
  for(const file of await readdir(music))if(/^k(\d+)-/.test(file)&&+file.match(/^k(\d+)-/)[1]>=16)await rm(join(music,file));
 }}};
}
