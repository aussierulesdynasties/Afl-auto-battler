p='scene.py'; s=open(p).read()
a=s.index('# courts as real geometry'); b=s.index('# AFL ovals outside the model')
blk=s[a:b]; s=s[:a]+s[b:]
old_mat=blk[blk.index('    def court_mat'):blk.index("    mats = {k: court_mat")]
new_mat='''    CC = {}
    def court_mat(nm, rgb):   # court_grain.png (0.25 m tile, stored / 1.25) x the court colour x1.25 carried in vertex colour
        fc = [1.25 * c for c in srgb(rgb)]
        if max(fc) > 1: print('WARN court colour over 1, clamped', nm, fc)
        m = mat_mul(nm, os.path.join(HERE, 'tex', 'court_grain.png'), 0.75); CC[m.name] = [min(1.0, c) for c in fc] + [1.0]
        return m
    def tint(ob):
        me = ob.data; set_corner_col(me, np.tile(CC[me.materials[0].name], (len(me.loops), 1))); return ob
'''
blk=blk.replace(old_mat,new_mat)
blk=blk.replace("set_uv_box(mk_obj('bg_court_slab_' + k, V, [[c, i, (i + 1) % c] for i in range(c)], mats[k]).data, 4.0)","set_uv_box(tint(mk_obj('bg_court_slab_' + k, V, [[c, i, (i + 1) % c] for i in range(c)], mats[k])).data, 4.0)")
blk=blk.replace("            mk_obj(nm, V, [[0, 1, 2, 3]], mat)","            set_uv_box(tint(mk_obj(nm, V, [[0, 1, 2, 3]], mat)).data, 4.0)")
e=s.index('# ---------- export background')
s=s[:e]+blk+s[e:]
open(p,'w').write(s)
