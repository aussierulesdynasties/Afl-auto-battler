# Blacktown's own pieces the ground kit has no kind for (kit/build.py calls build(kit, col) when blacktown.json names
# this file in "custom"). Plan positions in the model's metres (x east, y north, origin = the kit origin), heights above
# the field. Sources: Google Earth 3D mesh (straight-down shots and status-bar heights, whole metres) and close Google
# Earth obliques of the stand's back and roof (2026-11-22), the NSW 7.5 cm aerial for ground lines.
import math
import numpy as np
from mb import earclip, ccw

Z_GALLERY = 5.4       # top seat row and the gallery floor behind it (seat rows estimated from the 1,600 seats)
COL_STEP = 8.2        # back columns: 8 bays over the 66 m of the north half's back (Google Earth oblique)
MAST_STEP = 8.2       # roof masts along the spine (6 masts 8.1 m apart over the north 40 m, Google Earth top view)
MAST_FRAC = 0.42      # the spine: 42% of the roof's depth back from its front edge
MAST_H = 5.0          # mast tops read 16 m on Google Earth's status bar, the deck 11 m
LIGHT_STEP = 10.4     # twin floodlights under the roof's front edge (Google Earth oblique)
# the lower wing behind the south half of the stand: 8 m out from the roof's back edge, flat roof (Google Earth top view)
WING_B = (230.5, 255.5); WING_OUT = 8.0; WING_H = 8.0
# the indoor centre west of the stand: roof corners from the Google Earth top view (whole building turned about 6.5 deg)
IC_ROOF = [(-147.6, -19.6), (-122.5, -21.4), (-117.0, 31.9), (-140.9, 33.7)]
# heights from Google Earth's status bar on a 3 m grid (whole metres above the turf): the roof reads 6 m over its west two
# thirds and 7 m over the east third (a mono-pitch from 5.6 to 6.8 m fits every reading), the monitors 8 m, and a strip
# at each end reads 3 m (a lower annexe 5 m deep at the north end, 3.5 m at the south). The ground is 1 m below the turf.
# the raised walkway along the wing's outer face: Google Earth reads 2-3 m at its south end and 3-4 m at its north end,
# 2.5-7 m out from the wing; the obliques show solid parapet walls and a stair down to the ground at the south end
WALK_B = (235.0, 255.5); WALK_R = (2.5, 7.0); WALK_Z = (2.5, 3.5)
# concrete stairs straight up the bank from the fence to the path on top (Google Earth top view, 2025-07-24)
BANK_STAIRS = (100.0, 154.0); STAIR_W = 2.4
# near things no map has, from Google Earth's straight-down shots (2025-07-24): five water tanks 10 m across in a row
# north of the indoor centre and two containers beside them (Google Earth's status bar: tank tops and container roofs
# 2 m above the turf, the yard round them 1 m below it); two small white sheds south of it (OpenStreetMap outlines, 2.6 m by eye);
# the netted training field west of the indoor centre (corners from the top view, a 4 m fence, 6 m netting on the
# practice-net side) with its white wicket cover
# tank centres and sizes re-measured on the NSW aerial (2026-11-23; the Google Earth positions were 1-2 m east): four
# 10.2 m tanks and a 7.2 m one at the east end
TANKS = [((-144.8, 46.5), 5.1, 3.0), ((-134.0, 47.3), 5.1, 3.0), ((-123.0, 49.0), 5.1, 3.0), ((-112.8, 50.2), 5.1, 3.0), ((-103.0, 48.0), 3.6, 2.2)]; YARD_Z = -1.0   # centre, radius, wall height (the small one reads 1 m above the turf where the big ones read 2); YARD_Z = -1.0
# east of the tanks (straight-down Google Earth shot, 2025-07-24, 13 px a metre; status-bar heights 2026-11-23): a shed
# with a pale green roof reading 2 m above the turf (3 m over the yard), an open white-roofed canopy beside it reading 1-2 m
# (2.5 m over the yard) and a plant box on the shed's north-east corner; a red and a blue bin south of the tanks reading 1 m
YARD_SHED = [(-106.5, 52.5), (-100.8, 52.5), (-100.8, 58.2), (-106.5, 58.2)]; YARD_SHED_H = 3.0
YARD_CANOPY = [(-112.2, 55.4), (-106.9, 55.4), (-106.9, 58.2), (-112.2, 58.2)]; YARD_CANOPY_H = 2.5
YARD_PLANT = ((-101.95, 59.05), 2.3, 1.7, 1.5)   # centre, length (x), width (y), height
BINS = [((-110.05, 44.0), 'bin_red_bt'), ((-107.55, 43.95), 'bin_blue_bt')]; BIN = (1.9, 2.0, 1.8)
# the video screen and the empty frame beside it on the north-east bank (Google Earth 2025, an oblique from the field's
# south-west with the mouse stepped down each and the status bar read: 81 readings 2026-11-23): the screen's face runs
# from (45.9, 87.1) to (56.2, 78.4), solid from 4.5 m to 11.6 m above the turf with the bank seen under it, on two legs;
# the frame's two posts stand at (59.4, 73.8) and (65.6, 66.8), 12 m to its top beam, with a beam at 8 m and one at 5 m
# (the mesh reads open between them). The NSW aerial's tops agree within 0.6 m once its 1.5 m lean is taken off
SCREEN = ((45.9, 87.1), (56.2, 78.4), 4.5, 11.6, 0.8)          # left, right (face line), bottom, top, depth
FRAME = ((59.4, 73.8), (65.6, 66.8), 12.0, [(10.6, 12.0), (7.6, 8.4), (4.6, 5.4)], 0.5)   # posts, top, beams (z0, z1), section
# two shade sails over the grass between the baseball fields west of the car park: corners on a straight-down Google Earth
# shot (2025-07-24, 7.9 px a metre; the NSW aerial agrees within 1 m), heights from its status bar (2026-11-23: the west
# sail reads 3 m over its middle and 4 m at its south-east corner, the east one 3 m at its north end and 2 m at its
# south-east corner; the grass round them reads 0, the scene's ground there is the map's, held to it). Corner heights
# above the turf; each sail's edges curve in between its posts
SAILS = [[(-233.9, -161.9, 3.2), (-225.0, -159.6, 3.4), (-220.6, -177.0, 4.2), (-229.5, -178.9, 3.4)],
         [(-215.0, -158.8, 3.4), (-210.9, -158.1, 3.0), (-203.0, -173.3, 2.4), (-211.8, -175.2, 3.0)]]
CONTAINERS = [((-156.1, 49.2), 2.44), ((-153.1, 49.6), 2.44)]   # centre, width; 12.2 m long, 2.6 m high, along the row
SHEDS = [[(-126.3, -35.0), (-129.0, -35.9), (-126.8, -42.9), (-124.1, -42.0)], [(-118.7, -55.3), (-121.1, -56.6), (-117.1, -63.6), (-114.7, -62.2)]]
NETS = [(-198.9, 38.2), (-143.9, 30.7), (-147.4, -16.6), (-203.6, -9.4)]; NET_H = 4.0; NET_W = ((-200.6, 15.8), (-203.6, -8.4), 6.0)
COVER = [(-165.4, 11.8), (-150.2, 10.5), (-151.1, -14.1), (-167.8, -12.4)]
IC_W = 25.0; IC_ZW, IC_ZE = 5.6, 6.8; IC_OVER = 0.6; IC_PLINTH = 0.8; IC_BASE = -1.0
IC_ENDS = (2.5, 3.5, 3.3)              # south strip depth, north strip depth, their height
IC_EXT_S = 1.0                          # the south strip reaches 1 m past the roof corners seen from above (3 m readings)
IC_MON = (12.4, 8.0, 5, 12.5, 3.5, 8.0)   # roof monitors: first centre from the south roof edge, spacing, count, length, depth, top

# sealed ground round the indoor centre, traced on the NSW aerial (2026-11-23): the asphalt yard north of it and the
# service lane between it and the stand, the concrete plaza south of it, and the concrete paths (centre line, width).
# Laid 3-5 cm over the ground (the kit's terrain table there; beyond the kit's ground the scene's, held 0.15 m down)
ASPHALT = [[(-160.0, 34.6), (-126.0, 34.6), (-128.5, -27.5), (-110.5, -27.5), (-108.4, -20.0), (-106.4, 0.0), (-104.3, 36.0),
            (-101.0, 41.5), (-99.5, 63.0), (-112.0, 63.5), (-150.0, 57.5), (-160.0, 52.5)]]
CONCRETE = [[(-148.5, -21.0), (-128.5, -23.0), (-110.5, -27.5), (-108.3, -30.0), (-111.0, -36.0), (-107.0, -45.0), (-104.0, -52.0),
             (-106.0, -58.0), (-118.0, -60.0), (-125.0, -52.0), (-130.0, -47.5), (-146.0, -28.0), (-148.5, -27.0)],
            [(-176.0, -12.0), (-148.5, -12.0), (-148.5, -19.5), (-176.0, -19.5)]]   # the footpath west of the indoor centre
# the south fence: chain-link on the north edge of the long path round the south of the ground, from the kiosk out to
# the gate on the road. Its line through the lamp heads on the NSW aerial (the lamps stand in it); 3.0 m high from its
# posts' shadows (3.3-4.1 m, 11 posts) against the 5 m lamps' (5.9-6.4 m) on the same picture, which the indoor
# centre's 6-7 m wall and its shadow agree with (ratio about 1.2)
FENCE_S = [(-81.4, -107.1), (-72.4, -114.3), (-62.2, -120.6), (-52.2, -126.9), (-41.8, -132.2), (-30.6, -136.2),
           (-19.4, -139.4), (-3.0, -143.0)]; FENCE_S_H = 3.0
# the car park's light poles: their bases where their shadows start on the NSW aerial, heights from the shadows' length
# (11.3-12.6 m) over 1.25, the ratio the kiosk (3 m on Google Earth's status bar) and its shadow give on the same
# picture; one lamp head on top of each
LOT_POLES = [((-182.3, -83.9), 10.1), ((-179.1, -109.1), 9.6), ((-175.8, -133.7), 9.9), ((-166.4, -66.7), 9.6),
             ((-146.3, -79.3), 9.1), ((-142.9, -104.6), 9.0), ((-136.7, -154.1), 9.1), ((-133.4, -179.1), 9.3)]
# the concrete edge where the path to the car park crosses the drain (OpenStreetMap: a bridge): its line on the NSW
# aerial, the path at turf level and the ground south-east of it 1 m lower on Google Earth's status bar (15 readings),
# a 1.0-1.2 m face by its shadow, so it stands about 0.15 m proud of the path; no rail on it
EDGE_WALL = [(-148.2, -69.6), (-134.2, -57.0), (-130.6, -58.8)]; EDGE_UP = 0.15; EDGE_DROP = 1.0
# the low concrete slab south-west of the car park (the map and Overture have a 7 m building there): its edges on the
# NSW aerial, 1 m above the grass on Google Earth's status bar (5 readings on it, 0 round it) and 1.1 m by its shadow
SLAB = [(-218.5, -196.0), (-196.0, -192.0), (-191.5, -212.7), (-215.0, -215.8)]; SLAB_H = 1.1
PATHS_FAR = 2   # PATHS from this one on go in detail_far
PATHS = [([(-121.0, -55.0), (-117.0, -62.0), (-109.0, -77.0), (-101.0, -90.0), (-97.5, -97.5)], 4.5),
         ([(-100.0, -99.0), (-82.5, -84.0), (-78.0, -80.0)], 3.5),
         # the long path south of the fence: the sealed band runs 5-6.5 m south from the fence line on the NSW aerial
         # (grey runs every 3 m, 2026-11-23), out to the road footpath at the gate
         ([(-99.0, -100.5), (-91.5, -101.3), (-82.9, -109.3), (-73.9, -116.5), (-63.7, -122.8), (-53.7, -129.1), (-43.3, -134.4),
           (-32.1, -138.4), (-20.9, -141.6), (-4.5, -145.2), (-1.0, -146.0)], 5.2),
         ([(-129.0, -50.5), (-157.0, -70.0)], 5.6, 'asphalt_bt'),         # the wide sealed path south-west to the car park
         ([(-158.0, -67.5), (-185.0, -46.0)], 3.0)]                       # and the path north-west from its end
# lamp posts along the paths: their heads on the NSW aerial, 5 m posts with a short arm
# the kiosk where the south paths meet: roof corners on the NSW aerial (moved 0.4 m east for its lean), 3 m high on
# Google Earth's status bar (3 m grid, 13 cells)
KIOSK = [(-88.7, -90.0), (-83.9, -94.3), (-86.7, -97.7), (-91.6, -93.4)]; KIOSK_H = 3.0
LAMPS = [(-110.6, -73.4), (-104.3, -82.6), (-97.7, -90.7), (-90.0, -99.1)] + FENCE_S[:-1]; LAMP_H = 5.0
# the three low buildings south of the plaza (the map has one rough outline for all of them, left out of the backdrop by
# blacktown's drop_buildings): roof corners on the NSW aerial, moved east for its lean (0.5 m for the 3-4 m ones, 0.8 m
# for the big one), roof heights from Google Earth's status bar (2026-11-23, 25 readings, whole metres above the turf;
# the grass round them reads 0): the west block's mono-pitch roof 3 m on its west side and 4 m on its east, the link
# and the porch 3 m, the big block's roof 5 m along its north-east side, 6 m across the middle and 7-8 m along its
# south-west side (a mono-pitch from 5.4 to 7.8 m fits every reading but one). Plan, low-side height, high-side height,
# and the edge (two corner indices) the roof is low along; three roof vents on the big block from the aerial
SOUTH = [([(-113.9, -101.4), (-101.0, -104.0), (-104.9, -124.9), (-117.9, -122.3)], 3.3, 4.3, (3, 0)),
         ([(-101.8, -108.0), (-91.1, -115.4), (-95.9, -122.3), (-103.6, -117.5)], 3.1, 3.1, (0, 1)),
         ([(-95.9, -122.3), (-103.3, -127.5), (-103.3, -132.3)], 3.1, 3.1, (0, 1)),
         ([(-103.0, -132.3), (-90.8, -115.4), (-67.6, -131.6), (-80.5, -148.7)], 5.4, 7.8, (1, 2))]
SOUTH_VENTS = [(-96.6, -134.8), (-90.1, -139.3), (-85.0, -143.2)]
# the car park west of the indoor centre, from the NSW aerial (2026-11-23; Google Earth 2025-07-24 shows the same bays,
# empty): a lot 34 m across whose long axis runs 7.5 deg east of south from its north-west corner, in lot metres (s down
# the axis, w across it to the east): a row of bays along each side and a double row down the middle (5.5 m bays, 2.55 m
# apart, a 5.8-6 m aisle each side), hatched no-parking ends, a short row across the south end; the bus bay and the
# driveway up to the paths at the north end, the exit road south from the south-east corner
LOT_O = (-182.4, -75.6); LOT_A = (0.130, -0.9915)
LOT = [(0, 0), (0, 4.7), (-6.4, 5.6), (-6.2, 22.8), (-6.7, 34.1), (2.6, 28.6), (8.4, 28.0), (9.5, 34.0), (118, 34.0), (118, 28.0),
       (130, 27.8), (130, 19.8), (125, 20.0), (125, 6.0), (118, 0)]
LOT_ROWS = [(0.0, 5.5, 4.0, 108.0), (11.3, 16.85, 7.0, 108.0), (16.85, 22.4, 7.0, 108.0), (28.5, 34.0, 10.0, 112.0)]   # w0, w1, s0, s1
LOT_BAY = 2.55; LOT_SOUTH = (6.0, 20.0, 119.5, 125.0)   # the south row: w0, w1, s0, s1 (bays along s)
LOT_HATCH = [((108, 0), (118, 0), (118, 6), (108, 6)), ((112, 28.5), (118, 28.5), (118, 34), (112, 34))]
BUS_PATH = [(-177.7, -66.8), (-161.0, -66.8), (-161.0, -68.5), (-177.7, -68.5)]   # footpath along the bus bay
BUS_SHELTER = [(-171.3, -65.7), (-167.8, -65.7), (-167.8, -67.8), (-171.3, -67.8)]; BUS_SHELTER_H = 2.7   # height by eye


def build(k, col):
    S = next(s for s in k.D['stands'] if s['name'] == 'grandstand')
    mb = k.MB('detail'); up = np.array([0, 0, 1.0])
    zr0, zr1 = S['z_roof']; bs = k.brange(S)

    def geo(b):
        rf = k.fence_r(b % 360); ri, ro = k.interp(S['roof'], b); rs0 = rf + S['seat_front']; rb = ro - S['back_in']
        return rf, ri, ro, rs0 + S['seat_depth'], rb

    def rad(b): a = math.radians(b); return np.array([math.sin(a), math.cos(a), 0.0])

    # gallery floor behind the top row, its slab edge and parapet on the back line, the recessed ground-floor wall
    for i in range(len(bs) - 1):
        ba, bb = bs[i], bs[i + 1]; (_, _, _, la, ra), (_, _, _, lb, rbb) = geo(ba), geo(bb); bm = 0.5 * (ba + bb)
        k.oriented(mb, [k.P3(ba, la, Z_GALLERY), k.P3(bb, lb, Z_GALLERY), k.P3(bb, rbb, Z_GALLERY), k.P3(ba, ra, Z_GALLERY)], 'paving', up)
        k.oriented(mb, [k.P3(ba, ra, Z_GALLERY - 0.6), k.P3(bb, rbb, Z_GALLERY - 0.6), k.P3(bb, rbb - 2.5, Z_GALLERY - 0.6),
                        k.P3(ba, ra - 2.5, Z_GALLERY - 0.6)], 'render_bt', -up)                     # soffit of the overhang
        for r0, r1, z0, z1, sg in ((ra, rbb, Z_GALLERY - 0.6, Z_GALLERY + 1.0, 1),                    # slab edge + parapet, outside
                                   (ra - 0.2, rbb - 0.2, Z_GALLERY, Z_GALLERY + 1.0, -1),             # parapet, inside
                                   (ra - 2.5, rbb - 2.5, 0.0, Z_GALLERY - 0.6, 1)):                   # ground-floor wall
            k.oriented(mb, [k.P3(ba, r0, z0), k.P3(bb, r1, z0), k.P3(bb, r1, z1), k.P3(ba, r0, z1)], 'render_bt', sg * rad(bm))
        k.oriented(mb, [k.P3(ba, ra - 0.2, Z_GALLERY + 1.0), k.P3(bb, rbb - 0.2, Z_GALLERY + 1.0), k.P3(bb, rbb, Z_GALLERY + 1.0),
                        k.P3(ba, ra, Z_GALLERY + 1.0)], 'render_bt', up)
    # columns on the back line from the ground to the roof soffit, one every COL_STEP along the back
    def along(step, rfun, first):
        out = []; b = bs[0]; L = first
        while True:
            r = rfun(b); b2 = b + math.degrees(L / r)
            if b2 > bs[-1] - math.degrees(1.0 / r): break
            out.append(b2); b = b2; L = step
        return out
    for b in along(COL_STEP, lambda b: geo(b)[4], 2.0):
        c = k.pol(b, geo(b)[4] - 0.3); mb.box(c, 0.6, 0.6, zr0 - 0.5, 90 - b, 'render_bt')
    # roof masts: a steel post on the spine with a stay back and a stay forward to the deck
    deck = lambda b, f: (geo(b)[1] + f * (geo(b)[2] - geo(b)[1]), zr0 + f * (zr1 - zr0))
    for b in along(MAST_STEP, lambda b: deck(b, MAST_FRAC)[0], 3.0):
        r, z = deck(b, MAST_FRAC); top = k.P3(b, r, z + MAST_H)
        mb.beam(k.P3(b, r, z), top, 0.25, 0.25, 'steel_white')
        for f in (0.80, 0.15):
            rr, zz = deck(b, f); mb.beam(top, k.P3(b, rr, zz + 0.1), 0.08, 0.08, 'steel_white')
    # twin floodlights on brackets under the roof's front edge
    for b in along(LIGHT_STEP, lambda b: geo(b)[1], 5.0):
        r = geo(b)[1] + 0.6; t = np.array(k.pol(b + 90, 1.0))
        for s in (-0.35, 0.35):
            c = np.array(k.pol(b, r)) + t * s; mb.cyl(tuple(c), 0.22, zr0 - 1.05, zr0 - 0.55, 'lamps', n=12)
        mb.beam(k.P3(b, r - 0.3, zr0 - 0.5), k.P3(b, r + 0.3, zr0 - 0.5), 0.9, 0.12, 'steel_galv')
    wing(k, mb, S, geo, rad, up)
    walkway(k, mb, geo, rad, up)
    for b in BANK_STAIRS: bank_stair(k, mb, b)
    yard(k, mb, up)
    indoor(k, mb, up)
    keep = k.SHEAR[:]; k.SHEAR.clear(); south(k, mb); screen(k, mb); sails(k, mb); k.SHEAR[:] = keep
    mb.build(col)
    g = k.MB('surfaces'); f = k.MB('detail_far'); grounds(k, g, f); g.build(col); f.build(col)   # its own mesh: the game and the scene see it as ground
    # detail_far: the car park and the paths out to it, well past the model's own ground: the scene leaves it out of the
    # model's outline (run1.sh SKIP, BG_HULL_SKIP 'detail') so its trees and buildings beside them stay


# the backdrop scene's ground south-west of the indoor centre (bd_ground.json): its near-ground, road and car park meshes
# sampled straight down on a 2 m grid (2026-11-23). That ground is the real terrain eased to the field's level, so it does
# not move when the model changes; null where the model's own ground covers it
import json, os
_BD = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bd_ground.json')))


def _bd_z(x, y):
    fx = (x - _BD['x0']) / _BD['step']; fy = (y - _BD['y0']) / _BD['step']; Z = _BD['z']
    i, j = int(math.floor(fx)), int(math.floor(fy))
    if not (0 <= i < len(Z[0]) - 1 and 0 <= j < len(Z) - 1): return None
    c = [Z[j][i], Z[j][i + 1], Z[j + 1][i], Z[j + 1][i + 1]]
    if any(v is None for v in c):
        v = [q for q in c if q is not None]; return sum(v) / len(v) if v else None
    u, w = fx - i, fy - j
    return (c[0] * (1 - u) + c[1] * u) * (1 - w) + (c[2] * (1 - u) + c[3] * u) * w


def ground_z(k, x, y):
    """the ground under plan point (x, y): the kit's terrain inside its own ground (ground_r), the scene's beyond it"""
    b = math.degrees(math.atan2(x, y)) % 360; r = math.hypot(x, y)
    G = k.D['ground_r']; rg = float(np.interp(b, *zip(*G), period=360))
    if r <= rg: return k.terrain_z(b, r)
    z = _bd_z(x, y)
    return z if z is not None else -0.15


def drape(k, mb, poly, m, lift, step=2.0):
    """a flat-shaded sheet over the ground: the polygon cut into triangles no side longer than 'step', each corner on
    the ground plus 'lift'"""
    up = np.array([0, 0, 1.0])
    tris = earclip(ccw([tuple(p) for p in poly]))
    for t in tris:
        a, b, c = (np.array(p, float) for p in t)
        n = max(1, int(math.ceil(max(np.linalg.norm(b - a), np.linalg.norm(c - b), np.linalg.norm(a - c)) / step)))
        def P(i, j):   # barycentric grid point i along a->b, j along a->c
            q = a + (b - a) * i / n + (c - a) * j / n; return (float(q[0]), float(q[1]), ground_z(k, q[0], q[1]) + lift)
        for i in range(n):
            for j in range(n - i):
                k.oriented(mb, [P(i, j), P(i + 1, j), P(i, j + 1)], m, up)
                if i + j < n - 1: k.oriented(mb, [P(i + 1, j), P(i + 1, j + 1), P(i, j + 1)], m, up)


def grounds(k, mb, mf):
    """the sealed yard, lane, plaza and paths, and the lamp posts"""
    keep = k.SHEAR[:]; k.SHEAR.clear()   # plain polar geometry for the ground lookups
    for P in ASPHALT: drape(k, mb, P, 'asphalt_bt', 0.03)
    for P in CONCRETE: drape(k, mb, P, 'concrete_bt', 0.05)
    n = 0
    for i, (line, w, *m) in enumerate(PATHS):   # each leg its own slab, run on w/2 past both ends to fill the joints, each a little higher
        for a, b in zip(line, line[1:]):
            a, b = np.array(a, float), np.array(b, float); t = (b - a) / np.linalg.norm(b - a); q = np.array([-t[1], t[0]]) * w / 2
            a0, b0 = a - t * w / 2, b + t * w / 2
            drape(k, mf if i >= PATHS_FAR else mb, [tuple(a0 + q), tuple(b0 + q), tuple(b0 - q), tuple(a0 - q)], m[0] if m else 'concrete_bt', 0.06 + 0.004 * n); n += 1
    carpark(k, mf)
    z = min(ground_z(k, x, y) for x, y in SLAB); mf.prism(SLAB, z - 0.3, z + SLAB_H, 'concrete_bt', top='concrete_bt')
    for (x, y), h in LOT_POLES:
        z = ground_z(k, x, y)
        mf.cyl((x, y), 0.09, z, z + h, 'steel_galv', n=8)
        mf.box((x, y), 0.75, 0.4, 0.16, 0, 'steel_galv', z0=z + h - 0.16)
    for a, b in zip(EDGE_WALL, EDGE_WALL[1:]):   # 0.3 m thick, its top at the path's height plus EDGE_UP
        a, b = np.array(a, float), np.array(b, float); t = (b - a) / np.linalg.norm(b - a); q = np.array([t[1], -t[0]]) * 0.15
        za, zb = ground_z(k, *(a - q * 4)) + EDGE_UP, ground_z(k, *(b - q * 4)) + EDGE_UP
        P_ = [a - q, b - q, b + q, a + q]; Z_ = [za, zb, zb, za]
        k.oriented(mf, [(*P_[i], Z_[i]) for i in range(4)], 'concrete_bt', np.array([0, 0, 1.0]))
        for i, j, nn in ((0, 1, -q), (2, 3, q), (1, 2, t), (3, 0, -t)):
            k.oriented(mf, [(*P_[i], Z_[i] - EDGE_DROP - 0.4), (*P_[j], Z_[j] - EDGE_DROP - 0.4), (*P_[j], Z_[j]), (*P_[i], Z_[i])], 'concrete_bt', np.array([*nn, 0.0]))
    for x, y in LAMPS:
        z = ground_z(k, x, y)
        mb.cyl((x, y), 0.06, z, z + LAMP_H, 'steel_galv', n=8)
        mb.box((x + 0.35, y), 0.8, 0.22, 0.12, 0, 'steel_galv', z0=z + LAMP_H - 0.12)
    for a, b in zip(FENCE_S, FENCE_S[1:]):   # the south fence: mesh both ways, a post every 2.5 m
        a, b = np.array(a, float), np.array(b, float); d = b - a; L = np.linalg.norm(d); t = d / L; nn = np.array([t[1], -t[0], 0.0])
        nseg = max(1, int(math.ceil(L / 2.5)))
        for j in range(nseg):
            p, q = a + t * L * j / nseg, a + t * L * (j + 1) / nseg; zp, zq = ground_z(k, *p), ground_z(k, *q)
            for sg in (1, -1): k.oriented(mb, [(*p, zp), (*q, zq), (*q, zq + FENCE_S_H), (*p, zp + FENCE_S_H)], 'mesh', sg * nn)
            mb.cyl(tuple(p), 0.04, zp, zp + FENCE_S_H + 0.05, 'steel_galv', n=6)
    z = ground_z(k, *FENCE_S[-1]); mb.cyl(FENCE_S[-1], 0.04, z, z + FENCE_S_H + 0.05, 'steel_galv', n=6)
    z = min(ground_z(k, x, y) for x, y in KIOSK)
    mb.prism(KIOSK, z, z + KIOSK_H - 0.25, 'render_white_bt'); mb.prism(KIOSK, z + KIOSK_H - 0.25, z + KIOSK_H, 'roof_white_bt', top='roof_white_bt')
    k.SHEAR[:] = keep


def screen(k, mb):
    """the video screen on two legs, and the open steel frame beside it"""
    L, R, z0, z1, dp = SCREEN; L, R = np.array(L), np.array(R)
    c, u, n_in, wd = k.scoreboard(mb, L, R, -dp / 2, z0, z1, dp, 'board_back', 'board_back', [(0.0, 1.0, 'screen_off')], 0.3)
    ang = math.degrees(math.atan2(u[1], u[0]))
    for sg in (-1, 1):
        p = c + u * sg * (wd / 2 - 1.5); g = ground_z(k, *p)
        mb.box(tuple(p), 0.5, 0.5, z0 - g + 0.05, ang, 'steel_dark', z0=g - 0.3)
    A, B, top, beams, t = FRAME; A, B = np.array(A), np.array(B); u = (B - A) / np.linalg.norm(B - A); ang = math.degrees(math.atan2(u[1], u[0]))
    for p in (A, B):
        g = ground_z(k, *p); mb.box(tuple(p), t, t, top - g + 0.3, ang, 'steel_dark', z0=g - 0.3)
    for b0, b1 in beams:
        mb.box(tuple((A + B) / 2), np.linalg.norm(B - A) - t, t, b1 - b0, ang, 'steel_dark', z0=b0)


def sails(k, mb):
    """shade sails: a hypar between four post tops, its edges pulled in towards the middle, fabric both sides"""
    for S in SAILS:
        P = [np.array(p, float) for p in S]; C = np.mean(P, 0); n = 8
        def Q(u, v):
            b = (P[0] * (1 - u) + P[1] * u) * (1 - v) + (P[3] * (1 - u) + P[2] * u) * v
            f = 0.12 * (math.sin(math.pi * u) + math.sin(math.pi * v)); q = b + (C - b) * np.array([f, f, 0.0])
            return tuple(float(x) for x in q)
        for i in range(n):
            for j in range(n):
                q = [Q(i / n, j / n), Q((i + 1) / n, j / n), Q((i + 1) / n, (j + 1) / n), Q(i / n, (j + 1) / n)]
                k.oriented(mb, q, 'sail_blue_bt', np.array([0, 0, 1.0])); k.oriented(mb, [(x, y, z - 0.02) for x, y, z in q], 'sail_blue_bt', np.array([0, 0, -1.0]))
        for x, y, z in S:
            mb.cyl((x, y), 0.1, ground_z(k, x, y) - 0.3, z + 0.3, 'steel_galv', n=8)


def carpark(k, mb):
    """the car park: asphalt over the ground, white bay lines and hatching 12 cm wide, the bus bay's footpath and shelter"""
    O = np.array(LOT_O); A = np.array(LOT_A); W = np.array([-A[1], A[0]])
    if W[0] < 0: W = -W                                  # across the lot, to the east
    L = lambda s, w: tuple(O + A * s + W * w)
    drape(k, mb, [L(s, w) for s, w in LOT], 'asphalt_bt', 0.08)
    drape(k, mb, BUS_PATH, 'concrete_bt', 0.12)
    def line(p, q, lift=0.11):                            # a painted line as a thin strip on the asphalt
        p, q = np.array(p), np.array(q); t = (q - p) / np.linalg.norm(q - p); n = np.array([-t[1], t[0]]) * 0.06
        zz = [ground_z(k, *v) + lift for v in (p, q)]
        k.oriented(mb, [(*(p + n), zz[0]), (*(q + n), zz[1]), (*(q - n), zz[1]), (*(p - n), zz[0])], 'paint_white', np.array([0, 0, 1.0]))
    for w0, w1, s0, s1 in LOT_ROWS:
        s = s0
        while s <= s1 + 1e-6: line(L(s, w0), L(s, w1)); s += LOT_BAY
    line(L(7.0, 16.85), L(108.0, 16.85))                 # down the middle of the double row
    w0, w1, s0, s1 = LOT_SOUTH; w = w0
    while w <= w1 + 1e-6: line(L(s0, w), L(s1, w)); w += LOT_BAY
    for H in LOT_HATCH:
        P = [L(*p) for p in H]
        for a, b in zip(P, P[1:] + P[:1]): line(a, b)
        s0, w0 = H[0]; s1, w1 = H[2]; d = s0
        while d < s1:                                    # diagonal hatching 1.2 m apart
            line(L(d, w0), L(min(s1, d + (w1 - w0)), w0 + min(w1 - w0, s1 - d))); d += 1.2
    z = min(ground_z(k, *p) for p in BUS_SHELTER)
    (x0, y0), (x1, _), (_, y1) = BUS_SHELTER[0], BUS_SHELTER[1], BUS_SHELTER[2]
    for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)): mb.cyl((x, y), 0.05, z, z + BUS_SHELTER_H, 'steel_galv', n=8)
    mb.box(((x0 + x1) / 2, y0 - 0.05), x1 - x0, 0.08, BUS_SHELTER_H - 0.4, 0, 'steel_galv', z0=z + 0.2)   # back panel
    mb.prism(BUS_SHELTER, z + BUS_SHELTER_H, z + BUS_SHELTER_H + 0.12, 'roof_white_bt', top='roof_white_bt')


def south(k, mb):
    """the low buildings south of the plaza: rendered walls from 0.3 m below the ground to the roof, a mono-pitch roof
    with a 0.3 m fascia, roof vents"""
    up = np.array([0, 0, 1.0])
    for poly, zl, zh, (i0, i1) in SOUTH:
        P = [np.array(p, float) for p in poly]
        A, B = P[i0], P[i1]; t = (B - A) / np.linalg.norm(B - A); n = np.array([-t[1], t[0]])
        if np.dot(n, np.mean(P, 0) - A) < 0: n = -n
        depth = max(np.dot(p - A, n) for p in P)
        zr = lambda p: zl + (zh - zl) * max(0.0, np.dot(np.asarray(p) - A, n)) / depth
        g = min(ground_z(k, *p) for p in P)
        cen = np.mean(P, 0)
        for a, b in zip(P, P[1:] + P[:1]):
            e = b - a; nr = np.array([e[1], -e[0], 0.0])
            if np.dot(nr[:2], (a + b) / 2 - cen) < 0: nr = -nr
            k.oriented(mb, [(*a, g - 0.3), (*b, g - 0.3), (*b, zr(b)), (*a, zr(a))], 'render_white_bt', nr)
            k.oriented(mb, [(*a, zr(a)), (*b, zr(b)), (*b, zr(b) + 0.3), (*a, zr(a) + 0.3)], 'render_white_bt', nr)   # fascia
        for tri in earclip(ccw([tuple(p) for p in poly])):
            k.oriented(mb, [(x, y, zr((x, y)) + 0.3) for x, y in tri], 'roof_white_bt', up)
    poly, zl, zh, (i0, i1) = SOUTH[-1]
    P = [np.array(p, float) for p in poly]; A, B = P[i0], P[i1]; t = (B - A) / np.linalg.norm(B - A); n = np.array([-t[1], t[0]])
    if np.dot(n, np.mean(P, 0) - A) < 0: n = -n
    depth = max(np.dot(p - A, n) for p in P)
    for v in SOUTH_VENTS:
        z = zl + (zh - zl) * np.dot(np.array(v) - A, n) / depth + 0.3
        mb.cyl(v, 0.25, z - 0.1, z + 0.6, 'steel_galv', n=10)


def wing(k, mb, S, geo, rad, up):
    """two-storey wing on the back of the south half: walls from the stand's back line out to 8 m past the roof edge"""
    b0, b1 = WING_B; bs = [b0 + (b1 - b0) * i / 12 for i in range(13)]
    ri = lambda b: geo(b)[4] - 2.5; ro = lambda b: geo(b)[2] + WING_OUT
    for i in range(12):
        ba, bb = bs[i], bs[i + 1]; bm = 0.5 * (ba + bb)
        k.oriented(mb, [k.P3(ba, ro(ba), 0), k.P3(bb, ro(bb), 0), k.P3(bb, ro(bb), WING_H), k.P3(ba, ro(ba), WING_H)], 'render_bt', rad(bm))
        k.oriented(mb, [k.P3(ba, ri(ba), WING_H), k.P3(bb, ri(bb), WING_H), k.P3(bb, ro(bb), WING_H), k.P3(ba, ro(ba), WING_H)], 'roof_bt', up)
        # parapet 0.6 m round the roof's outer edge
        k.oriented(mb, [k.P3(ba, ro(ba) - 0.2, WING_H), k.P3(bb, ro(bb) - 0.2, WING_H), k.P3(bb, ro(bb) - 0.2, WING_H + 0.6),
                        k.P3(ba, ro(ba) - 0.2, WING_H + 0.6)], 'render_bt', -rad(bm))
        k.oriented(mb, [k.P3(ba, ro(ba), WING_H), k.P3(bb, ro(bb), WING_H), k.P3(bb, ro(bb), WING_H + 0.6), k.P3(ba, ro(ba), WING_H + 0.6)], 'render_bt', rad(bm))
        k.oriented(mb, [k.P3(ba, ro(ba) - 0.2, WING_H + 0.6), k.P3(bb, ro(bb) - 0.2, WING_H + 0.6), k.P3(bb, ro(bb), WING_H + 0.6),
                        k.P3(ba, ro(ba), WING_H + 0.6)], 'render_bt', up)
    for b, sg in ((b0, -1), (b1, 1)):   # the two ends
        t = np.array(k.pol(b + 90, 1.0)); n = np.array([*(t * sg), 0.0])
        k.oriented(mb, [k.P3(b, ri(b), 0), k.P3(b, ro(b), 0), k.P3(b, ro(b), WING_H + 0.6), k.P3(b, ri(b), WING_H + 0.6)], 'render_bt', n)
    # the sign on the outer face near the south end, 0.15 m proud in a frame
    bsg = b0 + math.degrees(8.0 / ro(b0)); r = ro(bsg) + 0.15; t = np.array(k.pol(bsg + 90, 1.0)); c = np.array(k.pol(bsg, r))
    for z0, z1, w, m, dr in ((1.9, 4.9, 9.4, 'board_back', 0.0), (2.05, 4.75, 9.1, 'screen_off', 0.05)):
        a, b_ = c - t * w / 2 + np.array(k.pol(bsg, dr)), c + t * w / 2 + np.array(k.pol(bsg, dr))
        k.oriented(mb, [(*a, z0), (*b_, z0), (*b_, z1), (*a, z1)], m, rad(bsg))


def walkway(k, mb, geo, rad, up):
    b0, b1 = WALK_B; n = 16; bs = [b0 + (b1 - b0) * i / n for i in range(n + 1)]
    base = lambda b: geo(b)[2] + WING_OUT; z = lambda b: WALK_Z[0] + (WALK_Z[1] - WALK_Z[0]) * (b - b0) / (b1 - b0)
    ri = lambda b: base(b) + WALK_R[0]; ro = lambda b: base(b) + WALK_R[1]
    for i in range(n):
        ba, bb = bs[i], bs[i + 1]; bm = 0.5 * (ba + bb); za, zb = z(ba), z(bb)
        k.oriented(mb, [k.P3(ba, ri(ba), za), k.P3(bb, ri(bb), zb), k.P3(bb, ro(bb), zb), k.P3(ba, ro(ba), za)], 'concrete_bt', up)
        for rr, sg, h in ((ro, 1, 1.1), (ri, -1, 1.1)):   # solid wall from the ground up to the parapet's top, each side
            k.oriented(mb, [k.P3(ba, rr(ba), 0.0), k.P3(bb, rr(bb), 0.0), k.P3(bb, rr(bb), zb + h), k.P3(ba, rr(ba), za + h)], 'conc_wall', sg * rad(bm))
            d = -0.2 * sg
            k.oriented(mb, [k.P3(ba, rr(ba) + d, za), k.P3(bb, rr(bb) + d, zb), k.P3(bb, rr(bb) + d, zb + h), k.P3(ba, rr(ba) + d, za + h)], 'conc_wall', -sg * rad(bm))
            k.oriented(mb, [k.P3(ba, rr(ba) + d, za + h), k.P3(bb, rr(bb) + d, zb + h), k.P3(bb, rr(bb), zb + h), k.P3(ba, rr(ba), za + h)], 'conc_wall', up)
    # north end wall; at the south end a straight stair down to the ground, 0.3 m treads, 0.17 m risers
    t1 = np.array(k.pol(b1 + 90, 1.0))
    k.oriented(mb, [k.P3(b1, ri(b1), 0), k.P3(b1, ro(b1), 0), k.P3(b1, ro(b1), z(b1) + 1.1), k.P3(b1, ri(b1), z(b1) + 1.1)], 'conc_wall', np.array([*t1, 0.0]))
    t = -np.array(k.pol(b0 + 90, 1.0)); A = np.array(k.pol(b0, ri(b0) + 0.2)); B = np.array(k.pol(b0, ro(b0) - 0.2)); z0 = z(b0)
    ns = int(round(z0 / 0.17)); w = np.linalg.norm(B - A); c = (A + B) / 2; ang = math.degrees(math.atan2(t[1], t[0]))
    for j in range(ns):
        zz = z0 - (j + 1) * z0 / ns; mb.box(tuple(c + t * (0.3 * j + 0.15)), 0.3, w, zz + z0 / ns, ang, 'conc_tread', mtop='conc_tread')
    nn = np.array([t[1], -t[0], 0.0])
    for e in (A, B):   # stair side walls, seen from both sides
        q0, q1 = e, e + t * 0.3 * ns
        for sg in (1, -1): k.oriented(mb, [(*q0, 0), (*q1, 0), (*q1, 1.0), (*q0, z0 + 1.1)], 'conc_wall', sg * nn)


def bank_stair(k, mb, b):
    """a flight of 0.5 m treads up the bank's measured slope, kerbs each side, a steel handrail down the middle"""
    fr = k.fence_r(b); r0, r1 = fr + 1.0, fr + 16.0; n = int((r1 - r0) / 0.5); u = np.array(k.pol(b, 1.0)); t = np.array(k.pol(b + 90, 1.0))
    ang = math.degrees(math.atan2(u[1], u[0])); zs = [k.terrain_z(b, r0 + (r1 - r0) * j / n) for j in range(n + 1)]
    for j in range(n):
        r = r0 + (r1 - r0) * (j + 0.5) / n; c = np.array(k.pol(b, r)); zt = max(zs[j], zs[j + 1]) + 0.05
        mb.box(tuple(c), (r1 - r0) / n, STAIR_W, zt - min(zs[j], zs[j + 1]) + 0.25, ang, 'conc_tread', z0=min(zs[j], zs[j + 1]) - 0.25, mtop='conc_tread')
        for sg in (-1, 1):
            mb.box(tuple(c + t * sg * (STAIR_W / 2 + 0.1)), (r1 - r0) / n, 0.2, zt + 0.2 - min(zs[j], zs[j + 1]) + 0.25, ang, 'conc_wall', z0=min(zs[j], zs[j + 1]) - 0.25)
    for j in range(0, n, 6):   # handrail posts, then the rail along their tops
        mb.box(tuple(k.pol(b, r0 + (r1 - r0) * j / n)), 0.06, 0.06, 0.95, ang, 'steel_galv', z0=zs[j])
    mb.beam(k.P3(b, r0, zs[0] + 0.95), k.P3(b, r1, zs[-1] + 0.95), 0.05, 0.05, 'steel_galv')


def yard(k, mb, up):
    for c, TANK_R, TANK_H in TANKS:   # tank wall, a shallow cone roof with a hatch
        mb.cyl(c, TANK_R, YARD_Z, YARD_Z + TANK_H, 'tank_bt', n=40)
        top = (c[0], c[1], YARD_Z + TANK_H + 0.5); ring = [(c[0] + TANK_R * math.cos(2 * math.pi * j / 40), c[1] + TANK_R * math.sin(2 * math.pi * j / 40)) for j in range(41)]
        for j in range(40):
            k.oriented(mb, [(*ring[j], YARD_Z + TANK_H), (*ring[j + 1], YARD_Z + TANK_H), top], 'tank_roof_bt', up)
        mb.box((c[0] - 2.0, c[1] + 1.0), 0.7, 0.7, 0.35, 0, 'steel_galv', z0=YARD_Z + TANK_H + 0.2)
    ang = 90 + 6.0   # the row runs about 6 deg north of east; containers stand across it
    for c, w in CONTAINERS:
        mb.box(c, 12.2, w, 2.6, ang, 'container_bt', z0=YARD_Z, mtop='container_roof_bt')
    for P in SHEDS:
        mb.prism(P, YARD_Z + 1.0, 2.6, 'render_white_bt', top='roof_white_bt')
    mb.prism(YARD_SHED, YARD_Z, YARD_Z + YARD_SHED_H - 0.15, 'render_white_bt')
    mb.prism(YARD_SHED, YARD_Z + YARD_SHED_H - 0.15, YARD_Z + YARD_SHED_H, 'roof_green_bt', top='roof_green_bt')
    for x, y in YARD_CANOPY: mb.cyl((x + (0.15 if x < -110 else -0.15), y + (0.15 if y < 56 else -0.15)), 0.05, YARD_Z, YARD_Z + YARD_CANOPY_H, 'steel_galv', n=8)
    mb.prism(YARD_CANOPY, YARD_Z + YARD_CANOPY_H, YARD_Z + YARD_CANOPY_H + 0.1, 'roof_white_bt', top='roof_white_bt', bot='roof_white_bt')
    c, L_, W_, h_ = YARD_PLANT; mb.box(c, L_, W_, h_, 0, 'steel_galv', z0=YARD_Z)
    for c, m in BINS: mb.box(c, BIN[0], BIN[1], BIN[2], 0, m, z0=YARD_Z, mtop=m)
    # the training field: chain-link round it, netting on the practice-net side, the wicket cover
    n = len(NETS)
    for i in range(n):
        a, b = np.array(NETS[i]), np.array(NETS[(i + 1) % n]); d = b - a; L = np.linalg.norm(d); t = d / L; nn = np.array([t[1], -t[0], 0.0])
        for sg in (1, -1): k.oriented(mb, [(*a, 0), (*b, 0), (*b, NET_H), (*a, NET_H)], 'mesh', sg * nn)
        for j in range(int(L / 3.0) + 1):
            mb.cyl(tuple(a + t * min(L, j * 3.0)), 0.04, 0, NET_H + 0.05, 'steel_galv', n=6)
    a, b, h = np.array(NET_W[0]), np.array(NET_W[1]), NET_W[2]; t = (b - a) / np.linalg.norm(b - a); nn = np.array([t[1], -t[0], 0.0])
    for sg in (1, -1): k.oriented(mb, [(*a, 0), (*b, 0), (*b, h), (*a, h)], 'mesh', sg * nn)
    for q in (a, b, (a + b) / 2): mb.cyl(tuple(q), 0.08, 0, h + 0.1, 'steel_galv', n=8)
    mb.prism(COVER, 0.0, 0.25, 'cover_bt', top='cover_bt')


def indoor(k, mb, up):
    """the indoor centre: a rectangle fitted to the roof corners seen from above, a mono-pitch roof rising to the east,
    rendered plinth and panels with a recessed glazed band under the eave on the west, a glazed east wall, modelled fins,
    five raised monitors (a dark louvred band under an overhanging cap), and the low strips at both ends"""
    R = np.array(IC_ROOF, float); c = R.mean(0); ax = (R[2] + R[3]) / 2 - (R[0] + R[1]) / 2; L = np.linalg.norm(ax); ax /= L
    cr = np.array([ax[1], -ax[0]])                       # across the building, pointing east
    O = c - ax * (L / 2 + IC_EXT_S) - cr * IC_W / 2; L += IC_EXT_S
    def P(u, v, z): q = O + ax * u + cr * v; return (float(q[0]), float(q[1]), z)
    def zr(v): return IC_ZW + (IC_ZE - IC_ZW) * v / IC_W   # roof top surface
    n3 = lambda d: np.array([*d, 0.0])
    def quad(a, b, m, nrm, z0a, z1a, z0b, z1b):            # wall from plan point a to b, bottom/top heights at each end
        k.oriented(mb, [(*a, z0a), (*b, z0b), (*b, z1b), (*a, z1a)], m, nrm)
    ds, dn, ze = IC_ENDS; u0, u1 = ds, L - dn; o = IC_OVER
    # the main hall's walls, inset o under the eaves
    pa = lambda u, v: (O + ax * u + cr * v)
    SW, SE, NE, NW = pa(u0, o), pa(u0, IC_W - o), pa(u1, IC_W - o), pa(u1, o)
    zg = IC_PLINTH + 0.55 * (zr(o) - IC_PLINTH)
    # west: plinth, panels, a glazed band 0.3 m back with fins
    quad(SW, NW, 'conc_wall', n3(-cr), IC_BASE, IC_PLINTH, IC_BASE, IC_PLINTH)
    quad(SW, NW, 'render_bt', n3(-cr), IC_PLINTH, zg, IC_PLINTH, zg)
    quad(SW + cr * 0.3, NW + cr * 0.3, 'glass_bt', n3(-cr), zg, zr(o), zg, zr(o))
    k.oriented(mb, [(*SW, zg), (*NW, zg), (*(NW + cr * 0.3), zg), (*(SW + cr * 0.3), zg)], 'render_bt', up)
    # east: glazed from the plinth to the eave, behind fins
    quad(NE, SE, 'conc_wall', n3(cr), IC_BASE, IC_PLINTH, IC_BASE, IC_PLINTH)
    quad(NE, SE, 'glass_bt', n3(cr), IC_PLINTH, zr(IC_W - o), IC_PLINTH, zr(IC_W - o))
    # the two ends (their top follows the roof's pitch)
    quad(SE, SW, 'render_bt', n3(-ax), IC_BASE, zr(IC_W - o), IC_BASE, zr(o))
    quad(NW, NE, 'render_bt', n3(ax), IC_BASE, zr(o), IC_BASE, zr(IC_W - o))
    ang = math.degrees(math.atan2(ax[1], ax[0]))
    for a, z0, z1, side in ((SW + cr * 0.3, zg, zr(o), -1), (SE, IC_PLINTH, zr(IC_W - o), 1)):   # fins 2.4 m apart
        n = int((u1 - u0) / 2.4)
        for j in range(1, n):
            f = a + ax * (u1 - u0) * j / n + cr * side * 0.2 * (1 if side > 0 else 0)
            mb.box(tuple(f + cr * side * 0.15), 0.12, 0.55, z1 - z0, ang, 'render_bt', z0=z0)
    # the roof: 0.5 m deep fascia all round, the top on the pitch
    C4 = [(0, 0), (L, 0), (L, IC_W), (0, IC_W)]
    k.oriented(mb, [P(u0, 0, zr(0)), P(u1, 0, zr(0)), P(u1, IC_W, zr(IC_W)), P(u0, IC_W, zr(IC_W))], 'roof_bt', up)
    k.oriented(mb, [P(u0, 0, zr(0) - 0.5), P(u0, IC_W, zr(IC_W) - 0.5), P(u1, IC_W, zr(IC_W) - 0.5), P(u1, 0, zr(0) - 0.5)], 'roof_soffit', -up)
    quad(pa(u0, 0), pa(u1, 0), 'fascia', n3(-cr), zr(0) - 0.5, zr(0), zr(0) - 0.5, zr(0))
    quad(pa(u1, IC_W), pa(u0, IC_W), 'fascia', n3(cr), zr(IC_W) - 0.5, zr(IC_W), zr(IC_W) - 0.5, zr(IC_W))
    quad(pa(u0, IC_W), pa(u0, 0), 'fascia', n3(-ax), zr(IC_W) - 0.5, zr(IC_W), zr(0) - 0.5, zr(0))
    quad(pa(u1, 0), pa(u1, IC_W), 'fascia', n3(ax), zr(0) - 0.5, zr(0), zr(IC_W) - 0.5, zr(IC_W))
    # the low strips at each end: rendered walls, a flat roof
    for ua, ub in ((0.0, u0), (u1, L)):
        poly = [tuple(pa(ua, 0.3)), tuple(pa(ub, 0.3)), tuple(pa(ub, IC_W - 0.3)), tuple(pa(ua, IC_W - 0.3))]
        mb.prism(poly, IC_BASE, ze - 0.4, 'render_bt')
        mb.prism([tuple(pa(ua, 0)), tuple(pa(ub, 0)), tuple(pa(ub, IC_W)), tuple(pa(ua, IC_W))], ze - 0.4, ze, 'fascia', top='roof_bt', bot='roof_soffit')
    # monitors across the roof
    m0, dm, nm, ml, md, mt = IC_MON; angc = math.degrees(math.atan2(cr[1], cr[0]))
    for j in range(nm):
        m = pa(m0 + j * dm, IC_W / 2 + 0.3); zb = zr(IC_W / 2) - 0.6; zc = mt - 0.4
        mb.box(tuple(m), ml - 0.4, md - 0.4, zc - zb, angc, 'glass_bt', z0=zb)
        for s_ in np.linspace(-1, 1, 9)[1:-1]:   # mullions in the louvred band
            mb.box(tuple(m + cr * s_ * (ml - 0.4) / 2), 0.08, md - 0.3, zc - zb, angc, 'render_bt', z0=zb)
        mb.box(tuple(m), ml, md, 0.4, angc, 'render_bt', z0=zc, mtop='roof_bt')
