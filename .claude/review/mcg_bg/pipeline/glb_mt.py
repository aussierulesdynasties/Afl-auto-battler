import json, struct, sys
for g in ('mcg', 'traeger'):
    b = open('out/%s/scene_bg.glb' % g, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; J = json.loads(b[20:20 + n])
    im, tx = J.get('images', []), J.get('textures', [])
    for m in J['materials']:
        if m['name'].startswith(('facade_tower', 'roof_', 'ground', 'court_slab', 'court_')):
            pb = m.get('pbrMetallicRoughness', {}); bt = pb.get('baseColorTexture')
            print(g, m['name'], 'tex', bt and im[tx[bt['index']]['source']].get('name'), 'factor', pb.get('baseColorFactor'), 'ext', m.get('extensions'))
    for me in J['meshes']:
        if me['name'].startswith(('bg_bld_tower', 'bg_roof', 'bg_court')): print(g, me['name'], sorted(me['primitives'][0]['attributes']))
