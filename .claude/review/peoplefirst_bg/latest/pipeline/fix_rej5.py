"""Lead's 3rd list: stripes only on OSM sports pitches; far land with structure; more haze."""
import json, shutil
s = open('bake_ground.py', encoding='utf-8', newline='').read(); shutil.copy('bake_ground.py', 'bake_ground_pre5.py')
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep("_st = 1 + 0.3 * (_st - 1)", "_st = 1 + 0.0 * (_st - 1)")   # no stripes in the shared detail tile (open land is rough)
rep("m_ = 2 * NE / S; R_ = np.random.default_rng(7)\n",
"""m_ = 2 * NE / S; R_ = np.random.default_rng(7)
import math
from PIL import ImageDraw
_sp = json.load(open(os.path.join(H, 'spec', name + '.json'))); _KX = 111320 * math.cos(math.radians(_sp['lat'])); _KY = 110540
PM = Image.new('L', (S, S), 0); _pd = ImageDraw.Draw(PM)
_js = json.load(open(os.path.join(H, 'data', name, 'osm.json'))); _js = _js['elements'] if isinstance(_js, dict) else _js
for el in _js:
    t = el.get('tags', {})
    if el.get('type') != 'way' or t.get('leisure') != 'pitch' or not el.get('geometry'): continue
    if t.get('surface', 'grass') not in ('grass', 'unknown') or any(k in t.get('sport', '') for k in ('tennis', 'basketball', 'netball', 'skate')): continue
    pts = [(((p['lon'] - _sp['lon']) * _KX + NE) / m_, (NE - (p['lat'] - _sp['lat']) * _KY) / m_) for p in el['geometry'] if p]
    if len(pts) > 2: _pd.polygon(pts, fill=255)
PM = np.asarray(PM.filter(ImageFilter.GaussianBlur(1.0 / m_)), np.float32) / 255; print('pitch px', int((PM > 0.5).sum()))
""")
rep("    f = 1 + 0.035 * np.tanh(3 * np.sin(2 * np.pi * sv / 12.0))",
    "    f = 1 + 0.05 * np.tanh(3 * np.sin(2 * np.pi * sv / 12.0)) * PM[rr]   # mown bands only on sports pitches")
open('bake_ground.py', 'w', encoding='utf-8', newline='').write(s)
sp = 'spec/peoplefirst.json'; d = json.load(open(sp)); d['haze_m'] = 9000; json.dump(d, open(sp, 'w')); print('ok')
