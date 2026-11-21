# House roofs (exec'd by scene.py when spec['roof_snap']): each house keeps the roof colour read off the aerial, snapped to
# the nearest real Australian roofing colour (Colorbond sheet or concrete/terracotta tile), so the pattern of the real street
# stays but the colours are true material colours, not hazy satellite greys. About 4 in 10 houses get a gable roof, the rest hip.
ROOFS = [  # sRGB, tile?
 ((166, 82, 54), True), ((132, 62, 44), True), ((150, 96, 70), True), ((104, 78, 62), True),   # terracotta, dark terracotta, apricot tile, brown concrete tile
 ((74, 76, 78), True), ((118, 118, 114), True),                                               # charcoal, grey concrete tile
 ((66, 68, 70), False), ((98, 102, 96), False), ((226, 226, 218), False), ((184, 184, 176), False),   # Monument, Woodland Grey, Surfmist, Shale Grey
 ((112, 90, 76), False), ((140, 142, 136), False), ((80, 74, 68), False), ((204, 192, 170), False),  # Jasper, Windspray, Ironstone, Paperbark
 ((150, 156, 158), False), ((54, 76, 64), False),                                              # zincalume, Cottage Green
]
_RP = np.array([c for c, _ in ROOFS], float)
_H = [b for b in BL if b['c'] == 'house' and b.get('roof_c')]
_S = np.array([b['roof_c'][:3] for b in _H], float); _m = _S.mean(0)
_S2 = _m + (_S - _m) * 1.5   # undo the aerial's haze before matching
_d = ((_S2[:, None, :] - _RP[None]) ** 2).sum(2) + rng.random((len(_S2), len(_RP))) * 900   # near ties go either way
for b, k in zip(_H, _d.argmin(1)):
    b['roof_c'] = list(ROOFS[k][0]); b['_tile'] = ROOFS[k][1]
for b in BL:
    if b['c'] == 'house': b['_gable'] = bool(rng.random() < 0.4)
import collections as _co; print('roof snap', len(_H), _co.Counter(int(k) for k in _d.argmin(1)).most_common())
