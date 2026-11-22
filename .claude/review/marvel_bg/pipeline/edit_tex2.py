"""Texture-session review 2026-11-20: curtain glass 12x14.4 m, far towers city_far, corrugated roofs, plaza pavers, water roughness."""
import json
P='scene.py'; s=open(P,newline='').read(); nl='\r\n' if '\r\n' in s else '\n'
def rep(a,b):
    global s
    a=a.replace('\n',nl); b=b.replace('\n',nl); assert s.count(a)==1, a[:60]; s=s.replace(a,b)
rep("def build_class(cls, tex, tw, th):\n", "def build_class(cls, tex, tw, th, sel=None, tag=''):\n")
rep("        if b['c'] != cls: continue\n", "        if b['c'] != cls: continue\n        if sel is not None and not sel(b): continue\n")
rep("    ob = mk_obj('bg_bld_' + cls,", "    ob = mk_obj('bg_bld_' + cls + tag,")
rep("        ro = mk_obj('bg_roof_%s_%s' % (cls, kind), rv, rf, mat_facade('roof_%s_%s' % (cls, kind), os.path.join(HERE, 'tex', 'roof_%s.png' % kind)))",
    "        ro = mk_obj('bg_roof_%s_%s%s' % (cls, kind, tag), rv, rf, mat_facade('roof_%s_%s%s' % (cls, kind, tag), os.path.join(HERE, 'tex', 'roof_%s.png' % ('corrugated' if kind == 'metal' else kind))))")
rep("build_class('tower', *spec.get('tower_tex', ['tower.png', 3.0, 3.6]))\n",
    "_FAR = spec.get('tower_far_m', 1e9)\n"
    "def _d(b): return float(np.hypot(*np.array(b['p'], float).mean(0)))\n"
    "build_class('tower', *spec.get('tower_tex', ['tower.png', 3.0, 3.6]), sel=lambda b: _d(b) <= _FAR)\n"
    "if 'tower_far_tex' in spec: build_class('tower', *spec['tower_far_tex'], sel=lambda b: _d(b) > _FAR, tag='_far')\n")
# pavers: detail texture switches to 6 m concrete pavers where the ground is painted path/paved
rep("_nt.links.new(_mx.outputs[2], _lift.inputs[6]); _nt.links.new(_lift.outputs[2], _b.inputs['Base Color'])\n",
    "_nt.links.new(_mx.outputs[2], _lift.inputs[6]); _nt.links.new(_lift.outputs[2], _b.inputs['Base Color'])\n"
    "_pm = os.path.join(D, 'pave_mask.png')\n"
    "if os.path.exists(_pm) and spec.get('pave_tex'):\n"
    "    _pt = _nt.nodes.new('ShaderNodeTexImage'); _pt.image = bpy.data.images.load(os.path.join(HERE, 'tex', spec['pave_tex'][0]))\n"
    "    _sc = _nt.nodes.new('ShaderNodeVectorMath'); _sc.operation = 'SCALE'; _sc.inputs['Scale'].default_value = 4.0 / spec['pave_tex'][1]\n"
    "    _nt.links.new(_uvd.outputs['UV'], _sc.inputs[0]); _nt.links.new(_sc.outputs[0], _pt.inputs['Vector'])\n"
    "    _mk = _nt.nodes.new('ShaderNodeTexImage'); _mk.image = bpy.data.images.load(_pm); _mk.image.colorspace_settings.name = 'Non-Color'\n"
    "    _mk.interpolation = 'Closest'\n"
    "    _nt.links.new(_dt.inputs['Vector'].links[0].from_socket if False else _nt.nodes['Image Texture'].outputs['Color'], _nt.nodes['Image Texture'].outputs['Color']) if False else None\n"
    "    _pl = _nt.nodes.new('ShaderNodeMix'); _pl.data_type = 'RGBA'; _pl.blend_type = 'MULTIPLY'; _pl.inputs['Factor'].default_value = 1.0\n"
    "    _pl.inputs[7].default_value = (255 / 192.1,) * 3 + (1,)   # pavers mean 192 -> keeps the painted value\n"
    "    _nt.links.new(_pt.outputs['Color'], _pl.inputs[6])\n"
    "    _sw = _nt.nodes.new('ShaderNodeMix'); _sw.data_type = 'RGBA'\n"
    "    _nt.links.new(_mk.outputs['Color'], _sw.inputs[0]); _nt.links.new(_dt.outputs['Color'], _sw.inputs[6]); _nt.links.new(_pl.outputs[2], _sw.inputs[7])\n"
    "    _sl = _nt.nodes.new('ShaderNodeMix'); _sl.data_type = 'RGBA'; _sl.inputs[6].default_value = (1.21,) * 3 + (1,); _sl.inputs[7].default_value = (1, 1, 1, 1)\n"
    "    _nt.links.new(_mk.outputs['Color'], _sl.inputs[0]); _nt.links.new(_sl.outputs[2], _lift.inputs[7])\n"
    "    _nt.links.new(_sw.outputs[2], _mx.inputs[7])\n")
rep("_wb.inputs['Roughness'].default_value = 0.15", "_wb.inputs['Roughness'].default_value = spec.get('water_rough', 0.15)")
open(P,'w',newline='').write(s)
J=json.load(open('spec/marvel.json'))
J['tower_tex']=['mv_curtain_glass.png',12.0,14.4]; J['tower_far_tex']=['mv_city_far.png',12.0,14.4]; J['tower_far_m']=1000
J['pave_tex']=['mv_plaza_pavers.png',6.0]; J['water_rough']=0.22
json.dump(J,open('spec/marvel.json','w'),indent=1); print('ok')
