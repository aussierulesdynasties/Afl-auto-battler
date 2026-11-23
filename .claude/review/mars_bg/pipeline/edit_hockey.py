p='prep.py'; s=open(p,newline='').read()
old="    json.dump({'slabs':"
new="""    HK = []
    for hx_, hy_ in spec.get('hockey_at', []):   # hockey pitch: OSM pitch outline nearest this point (layout traced on the satellite)
        for el in js:
            if el['type'] == 'way' and el.get('tags', {}).get('leisure') == 'pitch' and 'geometry' in el:
                pts = ring(el)
                if len(pts) >= 4 and pts[0] == pts[-1]:
                    cx = sum(q[0] for q in pts[:-1]) / (len(pts) - 1); cy = sum(q[1] for q in pts[:-1]) / (len(pts) - 1)
                    if math.hypot(cx - hx_, cy - hy_) < 15: HK.append(_obox(pts[:-1]))
    print('hockey', HK)
    json.dump({'hockey': HK, 'slabs':"""
assert old in s; s=s.replace(old,new)
s=s.replace("'pal': {k: PAL[k] for k in set(c for _, c in CT)}}", "'pal': dict({k: PAL[k] for k in set(c for _, c in CT)}, **{k: PAL[k] for k in ('turf_blue', 'turf_runoff') if k in PAL})}")
open(p,'w',newline='').write(s); print('ok')
