# Real land round every ground

Every ground used to stand on flat land: the ground models put their surrounds at height 0 and
the backdrops flattened a pad 150 m round the centre, blended to real land over the next 250 m.
That removed up to 29 m of real relief (North Hobart) and put Norwood's north rooftops 1.5 to 2 m
too high, because the real land falls 2 m from the ground to Beulah Road.

This tool gives every build tool the same measured bare-earth land: `terrain.py` (usage in its
header). The playing surface and the stands are not touched: they stay at turf level as built.

## The frame and the files

- Metres, x east and y north of the centre circle; height above the turf, so turf at the centre
  circle = 0. A model turned to its true bearing rotates its points into this frame first.
- `grids/<slug>.npz`: the near grid, ±1.5 km, rows south to north, columns west to east, heights
  in whole centimetres (`h_cm`, int32) and its metadata (`meta`, JSON: centre, step, source,
  licence). `terrain.load(slug).height(x, y)` reads it with bilinear interpolation.
- `terrain.py npy <slug> <dir>` writes it as float32 `.npy` + `.json` (the backdrop's format).
- `terrain.py far <slug>`: ±30 km at 60 m into the cache (`~/.cache/afl_terrain`), for horizons.
  Not committed (4 MB a ground); it rebuilds from the same tiles.
- `grounds.json`: each ground's centre (lat, lon of the centre circle), tile zoom and licence. A
  ground thread with a better measured centre corrects its own line.

## Source and why

Mapterhorn's terrain tiles (https://mapterhorn.com; source list in its repo's `source-catalog`).
They carry, re-gridded to 512 px web tiles:

| Where | Data | Cell | Licence |
|---|---|---|---|
| Mainland Australia (32 grounds) | Geoscience Australia, DEM of Australia derived from LiDAR 5 Metre Grid (bare earth) | 5 m (tiles 3.9 to 4.3 m) | CC BY 4.0 |
| Tasmania (Bellerive, York Park, North Hobart, Mac Point) | LIST Tasmanian 2 m DEM | 2 m (tiles 1.8 m) | CC BY 3.0 |
| Wellington (Sky Stadium) | LINZ 1 m LiDAR DEM | 1 m (tiles 1.2 m) | CC BY 4.0 |

Compared before choosing:

- **State 1 m LiDAR DEMs** are the best known source (Victoria, SA, WA, NSW 1 m). Of the open
  script services this machine reaches, only Queensland's is LiDAR at 1 m (NSW's is a 5 m
  stereo-photo model); Geoscience Australia's own services and ELVIS refuse
  this machine (CloudFront 403) and the PC's shell has no network. 1 m adds kerbs and steps, not
  slope: over a 50 m street the 5 m grid already holds the slope to a few centimetres.
- **The backdrops' old source (AWS Terrarium, z14)** mixes SRTM and other surface models: it reads
  buildings and noise (+44 m on the WACA's stands, -74 m near Subiaco). Rejected.
- **Copernicus GLO-30 / SRTM**: 30 m surface models with roofs and trees in them. Rejected near the
  grounds; GLO-30 is what Mapterhorn's zoom 12 falls back to outside the LiDAR, which matters only
  for far horizons.
- **FABDEM** (30 m, buildings and trees removed, CC BY-NC-SA; the game is not sold): the best
  open choice where no LiDAR exists. Too coarse to show a 1 to 2 m fall over a street.

## Limits, stated up front

- **No 5 m LiDAR tile for three grounds**: Mars Stadium (Ballarat), Traeger Park (Alice Springs)
  and Jiangwan (Shanghai). Their `grounds.json` lines say `pending`. Ballarat and Alice Springs
  have state LiDAR that this machine cannot reach yet; Shanghai has none open (FABDEM 30 m).
- Bare earth under buildings is interpolated by the data's makers; a basement ramp or a cutting
  narrower than 5 m is not in it.
- Water reads as the water level the survey flew on.
- The grid starts at the centre circle; the land inside a stadium's own outline is the model's
  business. Each build tool blends from its stadium's outline outward, never with a pad.

## How a building sits on the land

`Grid.footprint_base(poly)` returns the lowest land inside and along a footprint: the ground floor
sits there and the walls run down to it, so no wall hangs in the air on the low side and the high
side is dug into the slope, as real buildings on a slope are.

## Proof: measured against Google Earth (pass/fail, metres)

Height differences relative to the centre circle, Google Earth read from its status bar with the
mouse on each spot (whole metres, so ±0.5 m rounding). Pass: |ours - GE| ≤ 1.0 m (the rounding
plus 0.5 m). See `proof/` for each ground's table.
