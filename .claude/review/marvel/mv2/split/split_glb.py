# Split a glb into pieces by whole nodes / mesh primitives. Vertex, index, instance and image bytes are copied
# unchanged. A primitive too big for one piece is cut where the two triangle halves share no vertex
# (whole groups of seats): vertex bytes are sliced, the second half's indices drop by a constant.
import json, struct, sys, os
import numpy as np

src, outdir, stem, limit = sys.argv[1], sys.argv[2], sys.argv[3], int(float(sys.argv[4]))
b = open(src, 'rb').read()
n = struct.unpack('<I', b[12:16])[0]
j = json.loads(b[20:20 + n])
o = 20 + n
bin_ = b[o + 8:o + 8 + struct.unpack('<I', b[o:o + 4])[0]]
A, BV = j['accessors'], j['bufferViews']
TEXKEYS = {'baseColorTexture', 'metallicRoughnessTexture', 'normalTexture', 'occlusionTexture', 'emissiveTexture'}


def raw(bi):
    v = BV[bi]
    s = v.get('byteOffset', 0)
    return bin_[s:s + v['byteLength']]


def asz(a):
    return BV[A[a]['bufferView']]['byteLength']


def tex_refs(x, out):
    if isinstance(x, dict):
        for k, v in x.items():
            if (k in TEXKEYS or k.endswith('Texture')) and isinstance(v, dict) and 'index' in v:
                out.add(v['index'])
            tex_refs(v, out)
    elif isinstance(x, list):
        for v in x:
            tex_refs(v, out)
    return out


def mat_imgs(m):
    return {j['textures'][t]['source'] for t in tex_refs(j['materials'][m], set())}


units = []
for ni in j['scenes'][j.get('scene', 0)]['nodes']:
    nd = j['nodes'][ni]
    assert not nd.get('children')
    inst = list(nd.get('extensions', {}).get('EXT_mesh_gpu_instancing', {}).get('attributes', {}).values())
    for pi, p in enumerate(j['meshes'][nd['mesh']]['primitives']):
        accs = list(p['attributes'].values()) + [p['indices']]
        s = sum(asz(a) for a in accs) + sum(asz(a) for a in inst)
        if s <= limit * 0.8:
            units.append(dict(node=ni, prim=pi, cut=None, size=s))
            continue
        assert not inst
        ia = A[p['indices']]
        dt = {5125: '<u4', 5123: '<u2'}[ia['componentType']]
        idx = np.frombuffer(raw(ia['bufferView']), dtype=dt).reshape(-1, 3)
        mx = np.maximum.accumulate(idx.max(1))
        mn = np.minimum.accumulate(idx.min(1)[::-1])[::-1]
        cuts = np.where(mx[:-1] < mn[1:])[0]
        k = int(cuts[np.argmin(abs(cuts - len(idx) / 2))]) + 1
        V = int(mx[k - 1]) + 1
        nv = A[p['attributes']['POSITION']]['count']
        units.append(dict(node=ni, prim=pi, cut=(0, k, 0, V), size=s // 2))
        units.append(dict(node=ni, prim=pi, cut=(k, len(idx), V, nv), size=s // 2))

imgsize = {i: BV[im['bufferView']]['byteLength'] for i, im in enumerate(j.get('images', []))}


def uimgs(u):
    m = j['meshes'][j['nodes'][u['node']]['mesh']]['primitives'][u['prim']].get('material')
    return mat_imgs(m) if m is not None else set()


bins = []
for u in sorted(units, key=lambda u: -(u['size'] + sum(imgsize[i] for i in uimgs(u)))):
    best = None
    for bn in bins:
        add = u['size'] + sum(imgsize[i] for i in uimgs(u) - bn['imgs'])
        if bn['size'] + add <= limit and (best is None or add < best[1]):
            best = (bn, add)
    if best is None:
        bn = dict(units=[], imgs=set(), size=0)
        bins.append(bn)
        best = (bn, u['size'] + sum(imgsize[i] for i in uimgs(u)))
    bn, add = best
    bn['units'].append(u)
    bn['imgs'] |= uimgs(u)
    bn['size'] += add

for bi, bn in enumerate(bins):
    out = bytearray()
    nj = {'asset': j['asset'], 'scene': 0, 'scenes': [{'nodes': []}], 'nodes': [], 'meshes': [],
          'accessors': [], 'bufferViews': [], 'buffers': [{}]}
    if 'samplers' in j:
        nj['samplers'] = j['samplers']
    for k in ('extensionsUsed', 'extensionsRequired'):
        if k in j:
            nj[k] = j[k]

    def addbv(data, tmpl):
        while len(out) % 4:
            out.append(0)
        v = {kk: vv for kk, vv in tmpl.items() if kk not in ('byteOffset', 'byteLength', 'buffer')}
        v.update(buffer=0, byteOffset=len(out), byteLength=len(data))
        out.extend(data)
        nj['bufferViews'].append(v)
        return len(nj['bufferViews']) - 1

    amap = {}

    def addacc(a, sl=None, rebase=0):
        key = (a, sl, rebase)
        if key in amap:
            return amap[key]
        acc = dict(A[a])
        assert acc.get('byteOffset', 0) == 0
        v = BV[acc['bufferView']]
        data = raw(acc['bufferView'])
        if sl is not None:
            st = v.get('byteStride') or len(data) // acc['count']
            data = data[sl[0] * st:sl[1] * st]
            acc['count'] = sl[1] - sl[0]
            if acc['type'] == 'SCALAR':
                dt = {5125: '<u4', 5123: '<u2'}[acc['componentType']]
                data = (np.frombuffer(data, dtype=dt) - rebase).astype(dt).tobytes()
                acc.pop('min', None); acc.pop('max', None)
            elif 'min' in acc:
                arr = np.frombuffer(data, dtype='<f4').reshape(acc['count'], -1)
                acc['min'] = arr.min(0).tolist(); acc['max'] = arr.max(0).tolist()
        acc['bufferView'] = addbv(data, v)
        nj['accessors'].append(acc)
        amap[key] = len(nj['accessors']) - 1
        return amap[key]

    mmap, tmap, imap = {}, {}, {}

    def addimg(i):
        if i not in imap:
            im = dict(j['images'][i])
            im['bufferView'] = addbv(raw(im['bufferView']), BV[im['bufferView']])
            nj.setdefault('images', []).append(im)
            imap[i] = len(nj['images']) - 1
        return imap[i]

    def addtex(t):
        if t not in tmap:
            tx = dict(j['textures'][t])
            tx['source'] = addimg(tx['source'])
            nj.setdefault('textures', []).append(tx)
            tmap[t] = len(nj['textures']) - 1
        return tmap[t]

    def remap(x, key=None):
        if isinstance(x, dict):
            y = {k: remap(v, k) for k, v in x.items()}
            if key is not None and (key in TEXKEYS or key.endswith('Texture')) and 'index' in x:
                y['index'] = addtex(x['index'])
            return y
        if isinstance(x, list):
            return [remap(v) for v in x]
        return x

    def addmat(m):
        if m not in mmap:
            nj.setdefault('materials', []).append(remap(j['materials'][m]))
            mmap[m] = len(nj['materials']) - 1
        return mmap[m]

    bynode = {}
    for u in bn['units']:
        bynode.setdefault(u['node'], []).append(u)
    for ni in sorted(bynode):
        nd = j['nodes'][ni]
        mesh = j['meshes'][nd['mesh']]
        prims = []
        for u in sorted(bynode[ni], key=lambda u: (u['prim'], u['cut'] or ())):
            p = mesh['primitives'][u['prim']]
            q = dict(p)
            if u['cut']:
                t0, t1, v0, v1 = u['cut']
                q['attributes'] = {k: addacc(a, (v0, v1), 0) for k, a in p['attributes'].items()}
                q['indices'] = addacc(p['indices'], (t0 * 3, t1 * 3), v0)
            else:
                q['attributes'] = {k: addacc(a) for k, a in p['attributes'].items()}
                q['indices'] = addacc(p['indices'])
            if 'material' in p:
                q['material'] = addmat(p['material'])
            prims.append(q)
        m = dict(mesh)
        m['primitives'] = prims
        nj['meshes'].append(m)
        nn = json.loads(json.dumps(nd))
        nn['mesh'] = len(nj['meshes']) - 1
        ins = nn.get('extensions', {}).get('EXT_mesh_gpu_instancing')
        if ins:
            ins['attributes'] = {k: addacc(a) for k, a in ins['attributes'].items()}
        nj['nodes'].append(nn)
        nj['scenes'][0]['nodes'].append(len(nj['nodes']) - 1)
    while len(out) % 4:
        out.append(0)
    nj['buffers'][0]['byteLength'] = len(out)
    js = json.dumps(nj, separators=(',', ':')).encode()
    js += b' ' * ((4 - len(js) % 4) % 4)
    label = j['nodes'][max(bn['units'], key=lambda u: u['size'])['node']]['name'].lower().replace(' ', '_')
    nm = f"{stem}_{bi + 1}_{label}.glb"
    with open(os.path.join(outdir, nm), 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(out)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(out), 0x004E4942)); f.write(out)
    print(nm, 12 + 8 + len(js) + 8 + len(out), sorted(set(j['nodes'][u['node']]['name'] for u in bn['units'])))
