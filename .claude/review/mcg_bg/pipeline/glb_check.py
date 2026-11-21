import json, os, struct
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'mcg', 'scene_bg.glb')
b = open(p, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; g = json.loads(b[20:20 + n])
imgs = g.get('images', []); tex = g.get('textures', [])
for m in g['materials']:
    nm = m['name']
    if nm.startswith(('tree_', 'court_', 'ground')):
        pb = m.get('pbrMetallicRoughness', {}); bt = pb.get('baseColorTexture')
        img = imgs[tex[bt['index']]['source']].get('name') if bt else None
        nt = m.get('normalTexture'); nimg = imgs[tex[nt['index']]['source']].get('name') if nt else None
        print(nm, 'baseTex', img, 'texcoord', bt and bt.get('texCoord', 0), 'ext', bt and bt.get('extensions'), 'factor', pb.get('baseColorFactor', [1, 1, 1, 1]), 'normal', nimg)
for me in g['meshes']:
    if me['name'].startswith('bg_trees'):
        print(me['name'], sorted(me['primitives'][0]['attributes']))
print('extensionsUsed', g.get('extensionsUsed'))
