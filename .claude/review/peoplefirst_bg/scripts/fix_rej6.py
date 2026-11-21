s = open('bake_ground.py', encoding='utf-8', newline='').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:50]; s = s.replace(a, b)
rep("PM = Image.new('L', (S, S), 0); _pd = ImageDraw.Draw(PM)", "PM = Image.new('L', (S, S), 0); _pd = ImageDraw.Draw(PM); PL = Image.new('L', (S, S), 0); _pl = ImageDraw.Draw(PL); PA = [0.0]")
rep("    if len(pts) > 2: _pd.polygon(pts, fill=255)",
"""    if len(pts) > 2:
        _q = np.array(pts) * m_; _q = _q - _q.mean(0); _w, _v = np.linalg.eigh(_q.T @ _q); _ax = _v[:, -1]   # long axis of the pitch
        PA.append(math.atan2(-_ax[1], _ax[0])); _pd.polygon(pts, fill=255); _pl.polygon(pts, fill=min(255, len(PA) - 1))""")
rep("PM = np.asarray(PM.filter", "PL = np.asarray(PL); PA = np.array(PA); PM = np.asarray(PM.filter")
rep("    sv = X_ * np.cos(ang) + Y_ * np.sin(ang)", "    ang = np.where(PL[rr] > 0, PA[PL[rr]], ang)   # bands run along each pitch's long axis\n    sv = X_ * np.cos(ang) + Y_ * np.sin(ang)")
open('bake_ground.py', 'w', encoding='utf-8', newline='').write(s); print('ok')
