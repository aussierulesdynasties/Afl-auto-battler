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
- `terrain.py godot <slug>` writes `assets/grounds/<slug>/terrain.bin` for the game
  (`scripts/ui/match/GroundTerrain.gd`): 5 m cells to ±1 km and 20 m cells to ±3 km, int16
  centimetres, 0.5 MB. Only grounds whose surrounds ring the game draws itself
  (`GroundModels.SURROUNDS`) need it; the ring then follows the land, banking up from the model's
  street at `inner` over `LAND_BANK` (20 m), and its trees and buildings stand on it.
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
| Mars Stadium, Traeger Park, Jiangwan | FABDEM V1-2 (University of Bristol / Fathom), read from its official 10-degree zips by HTTP range | 30 m | CC BY-NC-SA 4.0 |

Checked: Mapterhorn's Norwood centre reads 55.386 m, Geoscience Australia's own 5 m service
(DEM_LiDAR_5m_2025 identify, read through the PC's browser) 55.3856 m: the same data.

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

- **Three grounds are on 30 m data, not LiDAR**: Mars Stadium (Ballarat), Traeger Park (Alice
  Springs) and Jiangwan (Shanghai) have no 5 m tile. They use FABDEM, which holds hills and
  valleys but not a 1 to 2 m fall across a single street. Alice Springs and Shanghai have no open
  LiDAR (ELVIS lists only SRTM for Alice Springs). Ballarat has Victoria's 2019 1 m LiDAR DEM
  (CC BY 4.0) in ELVIS, but its tiles refuse direct download, from the cloud and from the PC's
  browser alike (403); they come only through ELVIS's emailed order, which needs a person's email.
- **Bridges and decks are not land**: bare earth leaves out bridge decks and built-over decks
  (Federation Square over the rail yards reads as an 18 m pit, 1.3 km west of the MCG). Whoever
  builds the surrounds builds decks and bridges as structures on top; the land under them is
  real.
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
mouse on each spot (whole metres, read at the spot and at the centre circle, so up to 1 m of
rounding). Pass: every open-ground spot within 1.5 m (the rounding plus 0.5 m). Spots where Google
Earth reads a roof, a tree or a car are excluded and listed. See `proof/` for each ground's table.

| Ground | Spots | Ours - GE: mean, RMS, worst | Result |
|---|---|---|---|
| norwood | 26 of 36 (Norwood thread's grid) | +0.43, 0.54, 1.01 m | PASS |
| mcg | 6 of 9 | -0.17, 0.55, 0.80 m | PASS |
| marvel | 8 of 10 | +0.56, 0.60, 0.82 m | PASS |
| adelaide | 8 of 10 | -0.66, 0.77, 1.20 m | PASS |
| optus | 6 of 6 | +0.03, 0.24, 0.42 m | PASS |
| gmhba | 10 of 10 | +0.22, 0.35, 0.57 m | PASS |
| people_first | 6 of 6 | -0.00, 0.37, 0.50 m | PASS |
| mars | 7 of 7 | -0.00, 0.51, 0.85 m | PASS |
| traeger | 10 of 10 | +0.31, 0.47, 1.10 m | PASS |
| cazalys | 9 of 10 | +0.52, 0.56, 0.97 m | PASS |
| riverway | 8 of 8 | +0.49, 0.52, 0.77 m | PASS |
| accor | 9 of 10 | -0.31, 0.80, 1.63 m | FAIL |
| tio_darwin | 10 of 10 | +0.15, 0.27, 0.43 m | PASS |
| victoria_park | 9 of 10 | +0.48, 0.57, 1.00 m | PASS |
| scg | 8 of 9 | +0.07, 0.26, 0.38 m | PASS |
| engie | 8 of 10 | -0.49, 0.62, 0.90 m | PASS |
| bellerive | 8 of 8 | +0.06, 0.28, 0.70 m | PASS |
| manuka | 8 of 10 | -0.35, 0.45, 0.68 m | PASS |
| waverley_park | 9 of 10 | +0.69, 1.12, 2.56 m | FAIL |
| windy_hill | 9 of 10 | +0.35, 0.49, 0.72 m | PASS |
| moorabbin | 10 of 10 | -0.32, 0.40, 0.82 m | PASS |
| ikon_park | 9 of 9 | +1.85, 2.07, 3.28 m | FAIL |
| whitten | 10 of 10 | +0.92, 1.04, 2.20 m | FAIL |
| football_park | 9 of 10 | -0.06, 0.28, 0.65 m | PASS |
| subiaco | 8 of 10 | -0.44, 0.54, 0.78 m | PASS |
| waca | 8 of 9 | +0.15, 0.32, 0.55 m | PASS |
| york_park | 6 of 6 | +0.41, 0.48, 0.82 m | PASS |
| north_hobart | 10 of 10 | -0.21, 0.73, 2.15 m | FAIL |
| bruce | 4 of 4 | +0.45, 0.46, 0.57 m | PASS |
| barossa | 7 of 7 | +0.34, 0.68, 1.47 m | PASS |
| sky | 7 of 7 | -0.12, 0.25, 0.49 m | PASS |
| jiangwan | 6 of 10 | -1.01, 1.30, 2.52 m | FAIL |
| hands | 9 of 10 | +0.87, 0.91, 1.25 m | PASS |
| blacktown | 4 of 5 | -0.26, 0.40, 0.59 m | PASS |
| summit | 5 of 5 | -0.11, 0.87, 1.42 m | PASS |
| macpoint | 5 of 6 | -1.97, 2.00, 2.37 m | FAIL |
| gabba | 9 of 10 | -0.58, 0.64, 0.91 m | PASS |

**30 of 37 pass, 7 fail.** The fails are reported as measured; nothing was tuned to pass them.

- **Optus passes only after a fitted offset**: the LiDAR predates the stadium, and its six spots read a
  steady +2.0 m, so `turf_above_data_m` is 2.0. The offset came from the same six spots, so Optus's
  PASS is not an independent check.
- **Ikon Park** (+1.85 m mean, worst 3.3 m), **Whitten** (worst 2.2 m) and **Waverley Park** (worst 2.6 m):
  open, gently sloped roads (grade under 6 %) where Google Earth reads 2 to 3 m lower than the
  LiDAR; the LiDAR is self-consistent (Mapterhorn z12 and z14 agree) and Google Earth gives whole
  metres from its own, coarser terrain model. Which is wrong is not proven: a third source (the
  GA service by hand, or a surveyed mark) would settle it.
- **North Hobart**: one spot 2.15 m out on a 16 % slope (a few metres of position error is a metre or two there).
- **Accor**: one spot 1.63 m out on a smooth slope.
- **Mac Point**: a construction site; every spot reads 2 m low against its centre. The stadium's turf
  level is not set by the land survey; the Mac Point thread sets `turf_above_data_m` from the design.
- **Jiangwan**: FABDEM 30 m (no LiDAR); worst 2.5 m.
