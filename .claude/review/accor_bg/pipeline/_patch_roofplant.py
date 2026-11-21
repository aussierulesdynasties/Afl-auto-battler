import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
p = 'scene.py'; s = open(p, newline='').read()
a = "        else:\n            rf.append(tuple(r0 + i for i in range(k))); rcl += [rc] * k\n"
b = a + """            # rooftop plant: a few AC units / lift overruns on flat roofs, each its own size (breaks the plain lid)
            if cls != 'house' and b.get('a', 0) > 300:
                ang = math.atan2(e[1], e[0])
                for _ in range(int(min(6, 1 + b['a'] / 900))):
                    t_ = rng.random(2) * 0.5 + 0.25
                    q = P[rng.integers(k)] * (1 - t_[0]) + cxy * t_[0]
                    sx, sy, sz = rng.uniform(1.5, 5), rng.uniform(1.5, 4), rng.uniform(0.8, 2.6)
                    pc = rc * rng.uniform(0.6, 1.15)
                    cs = [(-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy)]
                    cs = [(q[0] + u * ct - v * st, q[1] + u * st + v * ct) for u, v in cs]
                    q0 = len(rv)
                    for x_, y_ in cs: rv.append((x_, y_, top)); ruv.append(ruv_(x_, y_))
                    for x_, y_ in cs: rv.append((x_, y_, top + sz)); ruv.append(ruv_(x_, y_ + sz))
                    for i_ in range(4):
                        j_ = (i_ + 1) % 4; rf.append((q0 + i_, q0 + j_, q0 + 4 + j_, q0 + 4 + i_)); rcl += [pc * 0.85] * 4
                    rf.append((q0 + 4, q0 + 5, q0 + 6, q0 + 7)); rcl += [pc] * 4
"""
assert a in s; s = s.replace(a, b, 1)
open(p, 'w', newline='').write(s)
r = open('rebuild_accor.sh', newline='').read()
if 'mk_accor_pavers' not in r:
    r = r.replace("mk_road_tex.py spec/accor.json &&", "mk_road_tex.py spec/accor.json && C:/Python314/python.exe -E mk_accor_pavers.py &&")
    open('rebuild_accor.sh', 'w', newline='').write(r)
print('ok')
