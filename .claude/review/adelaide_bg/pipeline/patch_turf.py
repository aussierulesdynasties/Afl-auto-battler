import json
H = 'D:/Temp/claude/b012626c2f559e8f/6855d913-d54b-43b8-92a6-1e4e1b34589b/scratchpad/proto/'
def sub(fn, a, b):
    s = open(H + fn, newline='').read()
    if '\r\n' in s: a, b = a.replace('\n', '\r\n'), b.replace('\n', '\r\n')
    assert s.count(a) == 1, (fn, a[:60], s.count(a))
    open(H + fn, 'w', newline='').write(s.replace(a, b))
# cricket square: a cut strip = the same mown grass, paler and drier
sub('scene.py', "mat_tint('cricket_square', os.path.join(_TX, 'adl_dry_grain.png'), (0.62, 0.62, 0.56), 0.9), 0.07, 6.0, seg=1.5)",
    "mat_tint('cricket_square', os.path.join(_TX, 'adl_oval_grass.png'), (1.35, 1.25, 0.95), 0.9), 0.07, 12.0, seg=1.5)")
s = json.load(open(H + 'spec/adelaide.json'))
# even turf over the open park around Oval No.2 (sat-traced, scene metres): courts/buildings are drawn later or as meshes; real paths are bg_paving meshes
s['paint_poly'] = s.get('paint_poly', []) + [['lawn', [[-310, 112], [-150, 112], [-138, 40], [-148, -60], [-160, -126], [-300, -126]]]]
json.dump(s, open(H + 'spec/adelaide.json', 'w'), indent=1); print('ok', len(s['paint_poly']))
