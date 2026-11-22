"""Orbit crops: white lines across the rail yard = footways painted AFTER the ballast (ways paint in OSM order).
Queue rail ballast/track paint and draw it after all other ways, so the yard surface covers paths painted across it."""
def sub(path, pairs):
    s = open(path, newline='').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, a[:60]); s = s.replace(a, b)
    open(path, 'w', newline='').write(s)
NL = '\r\n' if b'\r\n' in open('prep.py', 'rb').read() else '\n'
A = ("    if t.get('railway') in ('rail', 'light_rail', 'tram') and 'tunnel' not in t:" + NL +
     "        if t['railway'] == 'rail': dr.line(P(pts), fill=tuple(PAL.get('ballast_track', PAL['ballast'])), width=max(1, int(spec.get('ballast_track_m', 6) / PX)))" + NL +
     "        if t['railway'] != 'rail' or not spec.get('rail_geo'):" + NL +
     "            dr.line(P(pts), fill=tuple(PAL.get('track', PAL['road'])), width=max(1, int(1.8 / PX)))" + NL)
B = ("    if t.get('railway') in ('rail', 'light_rail', 'tram') and 'tunnel' not in t: RAILQ.append((t, P(pts)))" + NL +
     "for t, pp in RAILQ:   # rail paint last: the yard surface covers footways painted across it" + NL +
     "        if t['railway'] == 'rail': dr.line(pp, fill=tuple(PAL.get('ballast_track', PAL['ballast'])), width=max(1, int(spec.get('ballast_track_m', 6) / PX)))" + NL +
     "        if t['railway'] != 'rail' or not spec.get('rail_geo'):" + NL +
     "            dr.line(pp, fill=tuple(PAL.get('track', PAL['road'])), width=max(1, int(1.8 / PX)))" + NL)
sub('prep.py', [(A, B)])
s = open('prep.py', newline='').read(); i = s.index("for t, pp in RAILQ:")
j = s.rfind(NL + 'for ', 0, s.index("    hw = t.get('highway')")) + len(NL)   # the way loop header
s = s[:j] + 'RAILQ = []' + NL + s[j:]
open('prep.py', 'w', newline='').write(s); print('ok', s[j:j + 120].splitlines()[:2])
