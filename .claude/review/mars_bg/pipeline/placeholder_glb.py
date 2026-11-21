"""TEMP placeholder for the Mars ground model (OSM stadium outline, flat 0.3 m slab) until the builder's GLB exists.
blender -b -P placeholder_glb.py -- spec.json out.glb"""
import bpy, sys, json, math, bmesh
a = sys.argv[sys.argv.index('--') + 1:]
spec = json.load(open(a[0])); lat0, lon0 = spec['lat'], spec['lon']; KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
els = json.load(open('data/%s/osm.json' % spec['name'], encoding='utf-8'))['elements']
w = [e for e in els if e.get('tags', {}).get('leisure') == 'stadium' and 'Mars' in e['tags'].get('name', '')][0]
P = [((g['lon'] - lon0) * KX, (g['lat'] - lat0) * KY) for g in w['geometry']][:-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('placeholder'); bm = bmesh.new()
vs = [bm.verts.new((x, y, 0.3)) for x, y in P]; f = bm.faces.new(vs); bm.to_mesh(me)
o = bpy.data.objects.new('placeholder', me); bpy.context.scene.collection.objects.link(o)
bpy.ops.export_scene.gltf(filepath=a[1], export_format='GLB')
print('PLACEHOLDER', len(P), 'pts')
