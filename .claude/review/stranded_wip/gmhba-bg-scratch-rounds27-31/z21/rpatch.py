s = open('render.py', encoding='utf-8', newline='').read()
a = 'nt.links.new(bg.outputs["Background"], out.inputs["Surface"])'
assert a in s
s = s.replace(a, '''# camera rays see the blue gradient; lighting rays get a neutral, dimmer fill so ground shadows read grey, not blue glass
_fill = nt.nodes.new("ShaderNodeBackground"); _fill.inputs["Color"].default_value = (*job.get("fill", (0.60, 0.61, 0.62)), 1); _fill.inputs["Strength"].default_value = job.get("fill_strength", 0.75)
_lp = nt.nodes.new("ShaderNodeLightPath"); _mx = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(_lp.outputs["Is Camera Ray"], _mx.inputs[0]); nt.links.new(_fill.outputs["Background"], _mx.inputs[1]); nt.links.new(bg.outputs["Background"], _mx.inputs[2])
nt.links.new(_mx.outputs["Shader"], out.inputs["Surface"])''')
open('render.py', 'w', encoding='utf-8', newline='').write(s); print('ok')
s = open('pools.py', encoding='utf-8', newline='').read()
b = "        _box = (_A.min(0), _A.max(0), _zz)"
assert b in s
s = s.replace(b, b + "\n        _SINK.append((_A.copy(), _zz + 0.25))   # concourse: terrain under it drops 0.10 m below so it is never covered", 1)
# sink pass must run after the concourse is collected: move it to the end
i0 = s.index("    # basin cut:"); i1 = s.index("    if _FL[1]: mk_obj('bg_pool_floorlines'")
blk = s[i0:i1]; s = s[:i0] + s[i1:]
blk = "\n".join(l[4:] if l.startswith("    ") else l for l in blk.split("\n"))
j = s.index("    print('aquatic concourse'")
j = s.index("\n", j) + 1
s = s[:j] + "if _SINK:\n" + "\n".join(("    " + l) if l.strip() else l for l in blk.rstrip().split("\n")) + "\n" + s[j:]
open('pools.py', 'w', encoding='utf-8', newline='').write(s); print('ok2')
