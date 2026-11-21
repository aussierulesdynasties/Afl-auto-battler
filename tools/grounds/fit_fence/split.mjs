import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { prune } from '@gltf-transform/functions';
const [,, inp, outPrefix] = process.argv;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
for (const part of [0, 1]) {
  const doc = await io.read(inp);
  for (const mesh of doc.getRoot().listMeshes()) {
    const prims = mesh.listPrimitives();
    // balance by vertex count: greedy assignment
    const sizes = prims.map(p => p.getAttribute('POSITION').getCount());
    const order = sizes.map((s,i)=>i).sort((a,b)=>sizes[b]-sizes[a]);
    const tot=[0,0], who=[];
    for (const i of order) { const k = tot[0] <= tot[1] ? 0 : 1; who[i]=k; tot[k]+=sizes[i]; }
    prims.forEach((p,i)=>{ if (who[i] !== part) { mesh.removePrimitive(p); p.dispose(); } });
  }
  await doc.transform(prune());
  await io.write(`${outPrefix}_part${part+1}.glb`, doc);
}
