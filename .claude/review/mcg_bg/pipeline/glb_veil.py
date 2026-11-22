import json, os, struct
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'mcg', 'scene_bg.glb')
b = open(p, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; g = json.loads(b[20:20 + n])
for m in g['materials']:
    if 'veil' in m['name']:
        bt = m['pbrMetallicRoughness'].get('baseColorTexture'); t = g['textures'][bt['index']]
        print(m['name'], 'image', g['images'][t['source']]['name'], g['images'][t['source']].get('mimeType'), 'alphaMode', m.get('alphaMode'), 'cutoff', m.get('alphaCutoff'), 'factor', m['pbrMetallicRoughness'].get('baseColorFactor'), 'sampler', g['samplers'][t['sampler']] if 'sampler' in t else None)
