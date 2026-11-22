"""Director 2026-11-20 'Yes, trace + wall': inside the satellite square the water is the traced shoreline (shore.json
polygons) with a 3 m quay wall (water-1 to water+2) along it; outside, the old painted-water cells stay."""
P = 'scene.py'
s = open(P, newline='').read(); nl = '\r\n' if '\r\n' in s else '\n'
def rep(a, b):
    global s
    a = a.replace('\n', nl); b = b.replace('\n', nl); assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep("    Z[WG] = np.minimum(Z[WG], WZ - 3.0); Z[_rim] = np.maximum(Z[_rim], WZ + 2.0)\n",
    "    Z[WG] = np.minimum(Z[WG], WZ - 3.0); Z[_rim] = np.maximum(Z[_rim], WZ + 2.0)\n"
    "    SH = None\n"
    "    if os.path.exists(os.path.join(D, 'shore.json')):\n"
    "        _IN, _BED, _SAT = np.load(os.path.join(D, 'shore_grid.npy'))\n"
    "        Z[_SAT] = Z0_[_SAT] if False else np.where(WG[_SAT] | _rim[_SAT], WZ + 2.0, Z[_SAT])   # undo painted water inside the trace square\n"
    "        Z[_IN & ~_BED] = WZ - 0.2; Z[_BED] = WZ - 3.0\n"
    "        WG = (WG & ~_SAT) | _IN; WQ = WG & ~_SAT\n"
    "        SH = json.load(open(os.path.join(D, 'shore.json')))['polys']\n"
    "    else: WQ = WG\n")
rep("    _ix = np.argwhere(WG); wv = []; wf = []\n",
    "    _ix = np.argwhere(WQ); wv = []; wf = []\n")
rep("        wv += [(x0, y0, WZ), (x0 + NS, y0, WZ), (x0 + NS, y0 + NS, WZ), (x0, y0 + NS, WZ)]; wf.append((o, o + 1, o + 2, o + 3))\n",
    "        wv += [(x0, y0, WZ), (x0 + NS, y0, WZ), (x0 + NS, y0 + NS, WZ), (x0, y0 + NS, WZ)]; wf.append((o, o + 1, o + 2, o + 3))\n"
    "    qv = []; qf = []; quv = []\n"
    "    for poly in (SH or []):\n"
    "        o = len(wv); wv += [(x, y, WZ) for x, y in poly]; wf.append(tuple(range(o, o + len(poly))))\n"
    "        for k in range(len(poly)):\n"
    "            (ax, ay), (bx, by) = poly[k], poly[(k + 1) % len(poly)]\n"
    "            if max(abs(ax), abs(ay)) > 690 and max(abs(bx), abs(by)) > 690: continue   # edge of the traced square, not a shore\n"
    "            L_ = math.hypot(bx - ax, by - ay); o2 = len(qv)\n"
    "            qv += [(ax, ay, WZ - 1), (bx, by, WZ - 1), (bx, by, WZ + 2), (ax, ay, WZ + 2)]; qf.append((o2, o2 + 1, o2 + 2, o2 + 3))\n"
    "            quv += [(0, 0), (L_ / 4, 0), (L_ / 4, 0.75), (0, 0.75)]\n")
rep("    print('water cells', len(wf), 'z', WZ)\n",
    "    print('water cells', len(wf), 'z', WZ)\n"
    "    if qf:\n"
    "        qob = mk_obj('bg_quay', qv, qf, mat_img('quay', os.path.join(HERE, 'tex', 'wall.png'), 0.9))\n"
    "        set_uv(qob.data, np.array(quv, float)); print('quay faces', len(qf))\n")
s = s.replace("Z0_[_SAT] if False else ", "")
open(P, 'w', newline='').write(s); print('ok')
s = open(P, newline='').read()
a = "_wl = np.array(wf).ravel()"; assert s.count(a) == 1
s = s.replace(a, "_wl = np.concatenate([np.array(f_) for f_ in wf])"); open(P, 'w', newline='').write(s); print('ok2')
