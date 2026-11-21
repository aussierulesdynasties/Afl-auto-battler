// uninstance.mjs in.glb out.glb outdir colourname...: each node drawn with EXT_mesh_gpu_instancing becomes
// seat_tmpl_<colour>.bin (its mesh, unindexed float32 xyz) + seats_<colour>.bin (row-major 3x4 per instance),
// the format Oval3D's seats use; the node is removed from out.glb. Colour names are given in node order.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { prune } from '@gltf-transform/functions';
import fs from 'fs';
const [,, inp, out, dir, ...names] = process.argv;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc = await io.read(inp);
let k = 0;
function quatMat(q) { const [x,y,z,w]=q; return [
 [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
 [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
 [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]; }
for (const node of doc.getRoot().listNodes()) {
  const inst = node.getExtension('EXT_mesh_gpu_instancing');
  if (!inst) continue;
  const name = names[k++] ?? `inst${k}`;
  const W = node.getWorldMatrix(); // column-major 4x4
  const mesh = node.getMesh();
  const tri = [];
  for (const p of mesh.listPrimitives()) {
    const pos = p.getAttribute('POSITION'); const idx = p.getIndices();
    const n = idx ? idx.getCount() : pos.getCount();
    for (let i = 0; i < n; i++) { const v = pos.getElement(idx ? idx.getScalar(i) : i, []); tri.push(...v); }
    const mat = p.getMaterial(); const tex = mat?.getBaseColorTexture();
    console.log(name, 'material', mat?.getName(), 'factor', mat?.getBaseColorFactor().map(x=>x.toFixed(3)).join(','), 'tex', tex ? tex.getMimeType() : 'none');
    if (tex) fs.writeFileSync(`${dir}/${name}.${tex.getMimeType().split('/')[1]}`, tex.getImage());
  }
  fs.writeFileSync(`${dir}/seat_tmpl_${name}.bin`, Buffer.from(new Float32Array(tri).buffer));
  const T = inst.getAttribute('TRANSLATION'), R = inst.getAttribute('ROTATION'), Sc = inst.getAttribute('SCALE');
  const cnt = T.getCount(); const outm = new Float32Array(cnt * 12);
  for (let i = 0; i < cnt; i++) {
    const t = T.getElement(i, []), r = R ? R.getElement(i, []) : [0,0,0,1], s = Sc ? Sc.getElement(i, []) : [1,1,1];
    const m = quatMat(r);
    // local = [m*s | t]; world = W * local
    const L = [[m[0][0]*s[0], m[0][1]*s[1], m[0][2]*s[2], t[0]], [m[1][0]*s[0], m[1][1]*s[1], m[1][2]*s[2], t[1]], [m[2][0]*s[0], m[2][1]*s[1], m[2][2]*s[2], t[2]], [0,0,0,1]];
    const Wr = (r, c) => W[c * 4 + r];
    for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++) {
      let v = 0; for (let q = 0; q < 4; q++) v += Wr(r, q) * L[q][c];
      outm[i * 12 + r * 4 + c] = v;
    }
  }
  fs.writeFileSync(`${dir}/seats_${name}.bin`, Buffer.from(outm.buffer));
  console.log(name, cnt, 'instances,', tri.length / 9, 'triangles');
  node.dispose();
}
await doc.transform(prune());
await io.write(out, doc);
