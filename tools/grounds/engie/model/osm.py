# ENGIE Stadium plan data from OpenStreetMap (ODbL, (c) OpenStreetMap contributors) -> engie.json.
#   python3 osm.py [map.xml]   (without a file it downloads the area from the OSM API)
# Takes: the roof outline (way 395183095, building=grandstand: its inner edge is the roofs' front edge, its outer
# edge their back edge), the eight light masts (man_made=mast, tower:type=lighting) and the video wall
# (way 1098416479), and the stadium's site outline (way 4385854: the paved precinct round it). Everything else in engie.json (heights, the lean of the towers, the stands' sections) is
# modelled by eye from photos; nothing is measured off Google Earth or aerial imagery.
import sys, os, json, math, urllib.request
import xml.etree.ElementTree as ET
HERE = os.path.dirname(os.path.abspath(__file__))
LAT, LON = -33.8431119, 151.0676851          # the OSM AFL pitch's centre (way 320262641): the model's origin
BBOX = '151.0655,-33.8448,151.0700,-33.8414'


def load(path=None):
    if path:
        return ET.parse(path).getroot()
    with urllib.request.urlopen('https://api.openstreetmap.org/api/0.6/map?bbox=' + BBOX) as f:
        return ET.fromstring(f.read())


def main():
    t = load(sys.argv[1] if len(sys.argv) > 1 else None)
    N = {n.get('id'): (float(n.get('lat')), float(n.get('lon'))) for n in t.findall('node')}
    en = lambda la, lo: ((lo - LON) * 111320 * math.cos(math.radians(LAT)), (la - LAT) * 110574)
    pol = lambda e, n: (math.degrees(math.atan2(e, n)) % 360, math.hypot(e, n))
    way = {w.get('id'): w for w in t.findall('way')}
    ring = [pol(*en(*N[nd.get('ref')])) for nd in way['395183095'].findall('nd')]
    # the ring runs in along the front (bearings falling from ~5 to ~76) then out along the back (rising)
    i_out = max(range(len(ring) - 1), key=lambda i: ring[i + 1][1] - ring[i][1])     # the radial jump at ~77
    inner = ring[:i_out + 1]; outer = ring[i_out + 2:]   # (the point half way along the radial end is neither)
    unwrap = lambda pts: sorted(((b if b >= 70 else b + 360), round(r, 1)) for b, r in pts)
    rf = unwrap(inner[2:]); rb = unwrap(outer)
    masts = []
    for n in t.findall('node'):
        tags = {g.get('k'): g.get('v') for g in n.findall('tag')}
        if tags.get('man_made') == 'mast' and tags.get('tower:type') == 'lighting':
            e, n_ = en(*N[n.get('id')]); masts.append((round(pol(e, n_)[0], 1), round(e, 1), round(n_, 1)))
    vw = [pol(*en(*N[nd.get('ref')])) for nd in way['1098416479'].findall('nd')]
    # the stadium's site (way 4385854, leisure=stadium): its paved precinct, as a radius by bearing
    site = [pol(*en(*N[nd.get('ref')])) for nd in way['4385854'].findall('nd')]
    D_site = {}
    for k in range(0, 360, 2):
        # the site outline's radius where the ray at bearing k crosses it (the outline is star-shaped from 0, 0)
        best = None
        for (b0, r0_), (b1, r1_) in zip(site, site[1:]):
            d = (b1 - b0 + 180) % 360 - 180
            t = ((k - b0 + 180) % 360 - 180) / d if abs(d) > 1e-6 else -1
            if 0 <= t <= 1:
                r = r0_ + (r1_ - r0_) * t; best = r if best is None else max(best, r)
        D_site[k] = round(best, 1)
    D = json.load(open(os.path.join(HERE, 'engie.json')))
    # rf and rb are no longer taken from OSM: its grandstand way is 7 to 9 m small on the west and south
    # (Google Earth trace, tools/grounds/engie/fit); fit/tojson.py writes them as offsets of one fitted curve.
    D['osm_masts'] = sorted(masts)
    D['osm_video_wall'] = [[round(b, 1), round(r, 1)] for b, r in vw]
    D['site'] = [[k, r] for k, r in sorted(D_site.items())]
    json.dump(D, open(os.path.join(HERE, 'engie.json'), 'w'), indent=1)
    print('masts', sorted(masts)); print('video wall', vw)


if __name__ == '__main__':
    main()
