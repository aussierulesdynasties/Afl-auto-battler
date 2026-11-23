import json
p = 'roads_block.py'; s = open(p, newline='').read()
a = """        for q in Q: H_.setdefault((int(q[0] // CELL), int(q[1] // CELL)), []).append((ri, q[0], q[1], w))
    def _clear(ri, x, y):"""
assert a in s
s = s.replace(a, """        T = np.gradient(Q, axis=0); T = T / np.maximum(np.hypot(T[:, 0], T[:, 1]), 1e-6)[:, None]
        for q, tq in zip(Q, T): H_.setdefault((int(q[0] // CELL), int(q[1] // CELL)), []).append((ri, q[0], q[1], w, tq[0], tq[1]))
    def _clear(ri, x, y, tx, ty):   # a crossing road (more than 30 deg off this one's heading) blanks the lines near it""")
a = """                for rj, qx, qy, w in H_.get((cx + i, cy + j), ()):
                    if rj != ri and math.hypot(x - qx, y - qy) < w / 2 + 1.5: return False"""
assert a in s
s = s.replace(a, """                for rj, qx, qy, w, ux, uy in H_.get((cx + i, cy + j), ()):
                    if rj != ri and abs(tx * ux + ty * uy) < 0.866 and math.hypot(x - qx, y - qy) < w / 2 + 1.5: return False""")
a = """okl = _outside(Ql, 2.0) & np.array([_clear(ri, x, y) for x, y in Ql])"""
assert a in s
s = s.replace(a, """Tl = np.gradient(Ql, axis=0); Tl = Tl / np.maximum(np.hypot(Tl[:, 0], Tl[:, 1]), 1e-6)[:, None]
        okl = _outside(Ql, 2.0) & np.array([_clear(ri, x, y, a, b) for (x, y), (a, b) in zip(Ql, Tl)])""")
open(p, 'w', newline='').write(s)
sc = open('scene.py', newline='').read()
k = '# ---------- export background, then add the ground model for renders ----------'
assert k in sc and 'road_mesh' not in sc
open('scene.py', 'w', newline='').write(sc.replace(k, s + k))
sp = json.load(open('spec/peoplefirst.json')); sp['road_mesh'] = True; json.dump(sp, open('spec/peoplefirst.json', 'w'))
print('ok')
