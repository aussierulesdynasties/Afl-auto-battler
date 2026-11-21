"""Water streak test (texture session 2026-11-20): open scene.blend, change only the water colour, save a variant blend.
args: flat | soft | cur ; prints the colour texture's interpolation."""
import bpy, sys, os
mode = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.abspath(__file__))
nt = bpy.data.materials['water'].node_tree; b = nt.nodes['Principled BSDF']
tx = [n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image.name.startswith('mv_harbour_water')][0]
print('INTERP', tx.interpolation, 'normal interp', [n.interpolation for n in nt.nodes if n.type == 'TEX_IMAGE' and n is not tx])
mx = [n for n in nt.nodes if n.type == 'MIX'][0]
if mode == 'flat':
    nt.links.remove(mx.inputs[6].links[0]); mx.inputs[6].default_value = (*[(c / 255) ** 2.2 for c in (25, 50, 73)], 1)
elif mode == 'soft':
    tx.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'mv_harbour_water_soft.png'))
    uv = nt.nodes.new('ShaderNodeUVMap'); sc = nt.nodes.new('ShaderNodeVectorMath'); sc.operation = 'SCALE'
    sc.inputs['Scale'].default_value = 16.0 / 40.0   # mesh UVs are 16 m per unit -> 40 m per tile
    nt.links.new(uv.outputs['UV'], sc.inputs[0]); nt.links.new(sc.outputs[0], tx.inputs['Vector'])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'out', 'marvel', 'scene_w%s.blend' % mode))
print('SAVED', mode)
