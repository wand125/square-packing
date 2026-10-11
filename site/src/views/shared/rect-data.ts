// Share completed and in-flight requests across the desktop/phone layouts.
const requests = new Map<string, Promise<any>>();
function json(path: string) {
 if (!requests.has(path)) requests.set(path, fetch('data/rect/' + path).then(r => {
  if (!r.ok) throw new Error(`Rectangles data: ${r.status}`);
  return r.json();
 }).catch(error => { requests.delete(path); throw error; }));
 return requests.get(path)!;
}
export async function rectIndex(preview: boolean) {
 const index = await json('index.json');
 return {...index, ks: index.ks.filter(k => preview || k.k <= 15).map(k => ({...k, pieces: [], loaded: false}))};
}
export async function rectK(regions: any, k: number) {
 const edge = regions.ks.find(edge => edge.k === k);
 if (!edge) throw new Error(`Unavailable k: ${k}`);
 if (!edge.loaded) Object.assign(edge, await json(`k${k}.json`), {loaded: true});
 return edge;
}
