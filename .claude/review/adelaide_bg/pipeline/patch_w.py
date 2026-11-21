p='prep.py'; s=open(p,encoding='utf-8',newline='').read()
k='# hand-made grain: per-pixel value noise, never photo pixels'
add='''# River Torrens water: tile the hand-made water texture (texture session, ~40 m per tile) over water pixels
_wt = spec.get('water_tex')
if _wt:
    _a = np.asarray(img).astype(np.int16); _wm = np.all(np.abs(_a - np.array(PAL['water'])[None, None]) < 4, -1)
    _tp = max(2, int(round(_wt[1] / PX))); _t = np.asarray(Image.open(os.path.join(HERE, 'tex', _wt[0])).convert('RGB').resize((_tp, _tp), Image.LANCZOS))
    _til = np.tile(_t, (N // _tp + 1, N // _tp + 1, 1))[:N, :N]; _a = _a.astype(np.uint8); _a[_wm] = _til[_wm]; img = Image.fromarray(_a)
    print('water px', int(_wm.sum()))
'''
assert k in s and 'water_tex' not in s; s=s.replace(k, add+k,1); open(p,'w',encoding='utf-8',newline='').write(s)
p='scene.py'; s=open(p,encoding='utf-8',newline='').read()
o="build_class('house', 'wall.png', 3.6, 3.2)"
assert o in s; s=s.replace(o,"build_class('house', spec.get('house_wall_tex', 'wall.png'), 3.6, 3.2)",1); open(p,'w',encoding='utf-8',newline='').write(s)
import json; p='spec/adelaide.json'; j=json.load(open(p)); j['water_tex']=['adl_torrens_water.png',40]; j['house_wall_tex']='adl_bluestone.png'; j['palette']['walls_house']=[[88,92,98]] if 'palette' in j and 'walls_house' in j['palette'] else None; json.dump(j,open(p,'w'),indent=1)
