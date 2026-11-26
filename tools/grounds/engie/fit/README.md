# ENGIE plan and heights from Google Earth (2026-11-22)

Measures the stadium from Google Earth and writes the plan into `../model/engie.json`. The Google Earth shots stay
in a work folder (`ge/`, with `cal.json`) and are never committed or baked into a texture. Run every script from
that folder: `python3 <repo>/tools/grounds/engie/fit/<script>.py`.

## Scale and traces

1. Scale: two top-down shots (3000 m, 7y) 60 m apart. `cv2.phaseCorrelate` gives 0.364 m per pixel (0.363 and
   0.365 from the north and south pairs). OSM's pitch outline turned out 4.5% too big against it.
2. `seg.py`, `trace.py`: the sunlit field mask (`field.npy`) and the registration offset to the model's origin.
3. `trace2.py`, `edges.py`: whiteness (the darkest colour channel) along rays every 0.5 degrees in three shots
   (centre, 60 m north and 60 m south). These give the roof front and back edges (`edges.json`).
4. `relief.py`: a top-down shot from 3000 m shows a roof edge 18 to 25 m up about 0.6 m further out than it is
   (z/H from the nadir). It moves the traced roof edges back in (`edges_true.json`).
5. `cornerE.py`: the east roof's front edge at its north end (72 to 86 degrees), where the general trace stopped
   on a pale landing in front of the roof.
6. `fieldshadow.py`: the west and north field edge, which is in shade in Google Earth: the step from shaded turf to
   the brighter apron, the first one out from the turf, 1 to 11 m inside the stand front.

## Fits (order: fit2, arcs, corner_arc, comp_rings, roofends; fieldshadow then needs one more round)

- `fit2.py`: the field edge, a 5-harmonic polar curve fitted to the sunlit and the shaded field edge; and the 1998
  bowl, a 6-harmonic polar curve fitted to the old stands' roof front, its roof back an exact normal offset
  (25.81 m).
- `composite.py`, `arcs.py`: the 2012 north and east roof edges are not straight and do not follow the bowl. Each is
  a circular arc, tangent to the bowl ring at a join inside its tower gap (the best join found there).
- `corner_arc.py`: the east roof front is two arcs: 66 m radius from the south-east tower gap, then 123 m from
  122 degrees to the open end, tangent to each other.
- `comp_rings.py`: writes fence (the field edge), rf, rb and stand_front (rf less 1.6 m) into engie.json, with
  the curves themselves under `outline`, and prints the fit error per stand.
- `roofends.py`: the north and east roofs end square beside the open end. The bearing where the sheet ends, on 8
  arcs across each roof, fitted with a straight line (`roof_ends` on those stands).

Fit error, 2026-11-22 (metres, radial, gross mistraces over 4 m counted and left out):

| Edge | rms | 95% |
| --- | --- | --- |
| Field edge, sunlit (east, south) | 0.91 | 2.12 |
| Field edge, shaded (west, north) | 1.28 | 2.98 |
| Roof front: north / east / SE / S / SW / W / NW | 0.54 / 0.31 / 0.11 / 0.70 / 0.86 / 0.21 / 0.30 | up to 2.35 |
| Roof back: north / east / SE / S / SW / W / NW | 0.61 / 0.34 / 0.10 / 0.21 / 0.56 / 0.19 / 1.28 | up to 3.08 |
| Roof ends beside the open end | 0.1 | |
| East stand front row against the model's | 0.41 | 0.72 |

The NW roof back's 1.28 m is a 5 degree stretch where the trace runs onto the tower's gap block.

## Heights

`stereo.py`, `heights.py`: two top-down stereo pairs (1500 m, 15y, 150 m baselines east-west and north-south),
StereoSGBM, and heights over the field from the disparity. Old roof segments 21.5 m at the front and 18.3 m at
the back at their ends, arching 3.2 m mid-span. North and east (2012) roofs: 18 to 21.5 m at the front, 18 m at the
back. The two pairs agree within about 1 m. `gap.py`, `seatfront.py`: the field edge to the first seats.

## Side check from the obliques

`obmeasure.py <repo>/tools/grounds/engie/model/build.py OUT`: projects the shipped model's field edge, roof front,
roof back and wall base into the four matched obliques (`ob_000/090/180/270.png`: 1200 m, tilt 50, f 3859 px), and
along each finds the strongest image edge of the expected kind within 5 m (4 m for the wall base). The one free
number per view is Google Earth's aim height over the field. Offsets in metres along the ground, outward positive:

| Line | points | median | rms | within 2 m |
| --- | --- | --- | --- | --- |
| Field edge | 827 | +0.9 | 1.47 | 85% |
| Roof front | 951 | -0.6 | 1.64 | 80% |
| Roof back | 1,902 | -0.5 | 1.84 | 74% |
| Wall base | 898 | -0.9 | 2.57 | 44% |

## Limits

- The scale holds to about 1%.
- Row counts and tier lines under the roofs cannot be seen from above. The stand's rows follow the measured front
  row back to the outside wall, which is taken as 1.5 m inside the roof's back edge. Where that is shallower (the
  north and east stands' ends), the upper tier has fewer rows.
- The wall base is too dim under the roof overhang to measure better than about 2.5 m in the obliques, and the
  views disagree on its sign, so the 1.5 m overhang is not confirmed.
- One view (heading 180) puts the south roofs about 1.3 m further in than the other three views and the top-down
  trace do. That is likely the Google Earth mesh or camera, not the model, but it is not settled.
