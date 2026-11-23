# Ground kit: first-draft stadiums from the satellite

Row 202 step 2b (rule 2.90). A shared version of the Riverway build (`riverway/model/build.py`, `mb.py`, `paint.py`,
`proofs.py`) so a new ground is a JSON plan, not a new set of scripts. Used for Barossa Park, Hands Oval, Sky Stadium,
Blacktown, Summit Park, Jiangwan Stadium and Macquarie Point (first drafts, 2026-11-20).

A ground lives in `tools/grounds/<slug>/`: `model/<slug>.json` (the plan), and after a build `model/<slug>.glb`,
`model/seat_tmpl.bin`, `model/seats_<colour>.bin` (the format `Oval3D._ground_model` reads). Satellite tiles, textures
and renders are rebuilt on demand and git-ignored.

## Steps

1. `python3 kit/sat.py <dir>`: satellite mosaic (Google tiles, z19, 0.25 m/px) round `lat`/`lon` -> `work/sat.png`.
2. Fence: `python3 kit/fence.py <dir> r0 r1` traces the field's grass edge and fits an ellipse; where it is fooled
   (banks, shadows) pick points on the fence by hand from `kit/plan.py` and fit them with `python3 kit/fit.py x y ...`.
   `python3 kit/recentre.py <dir> x0 y0 a1 a2 rot` moves the origin to the fence centre and refetches the mosaic.
3. Trace on `python3 kit/plan.py <dir> [x0 y0 x1 y1] [out.png]` (metre grid, the plan drawn over the satellite).
   Bowl roofs: `python3 kit/edges.py <dir> b0 b1` reads roof edges per bearing.
4. `python3 kit/clear.py <dir>`: every stand front, building, tower and screen must sit outside the boundary fence
   (a straight stand's chord cuts inside a curved fence unless it is set back).
5. `BLENDER=<blender 5.2> kit/make.sh <slug>`: textures, GLB and seat files into `model/`, proofs into `render/`,
   review boards into `.claude/review/<slug>/` (top-down over the satellite, turntable stills, seats and boundary
   views, an orbit film).

## The plan (`<slug>.json`)

- `lat`, `lon` (origin = fence centre), `half` (mosaic half-width, m), `fence` [x0, y0, a1, a2, rot deg], `fence_h`,
  `fence_mat` (`mesh` chain-link, `pickets`, or any painted material), `fence_cap`.
- `stands`: `straight` (a straight stand: front edge `a`-`b`, `depth`, `z_seat`, optional skillion `roof`), the
  Riverway polar kinds `single`, `two_tier`, `open` (optional `front_tab`, `no_seats`), `block`, and `bank` (grass hill).
  Seat colours per stand: `row_cols` (front to back) or `seat_mix`.
- `towers`, `extras` (`polys`, `boxes`, `buildings`, `sails`, `shelters`, `screen`), `rings` (a running track),
  `dome` (a whole-ground translucent roof on ribs), `outer_r` (number or [b, r] table), `path_w` (number or [b, w]
  table), `ground_r` (where the ground ends: number, default 240, or a [b, r] table; with a table the rest out to
  240 m is a separate flat mesh `concourse_far`, which the game hides under a backdrop), `mats_ground`.
- Optional: `fence_fourier` {c, a0, ab} (the fence as one smooth polar Fourier curve fitted to a trace, in place of the
  ellipse); `terrain` {b, dr, z} (ground heights at distances `dr` beyond the fence on bearings `b`: the bank and path
  follow it); per stand `open_back` (no back walls: an open colonnade, modelled in the ground's own file) and
  `end_skew` {b, deg, ramp} (a stand end cut on a line that isn't radial); `custom` (a file in `model/` whose
  `build(kit, col)` adds the ground's own pieces, e.g. `blacktown/model/detail.py`).
- `paint`: the ground's own textures by kind (see `kit/paint.py`). Every texture is painted in code: no photo pixels.

6. Copy the GLB and seat files into `assets/grounds/<slug>/`, re-import (`godot --headless --import`), then hold the seats
   to the shared seat rule: `godot --headless --path . --script tools/grounds/seat_check.gd -- --write <slug>` takes out
   any seat with no floor, no headroom (2 m over its tread), inside the fence or left alone, and
   `tests/run_ground_seats_tests.gd` fails a ground that breaks it. `tools/grounds/seat_shots.gd` films the failing seats.

Seats sit on each row's own radial line (`seat_rows`), as the treads are drawn; until 2026-11-21 each row stepped along
the row's normal instead, which walks off the treads where the bowl is not round (Sky Stadium's upper deck sat a tread
up, sunk into the concrete with its pans through the concourse ceiling).

New seat colour names go in `SEAT_COLOURS` in `scripts/ui/match/Oval3D.gd` (the build prints each mean).

Stadium only, as for the other grounds: no turf, goalposts, nets, sponsor boards, lettering or crowd.
