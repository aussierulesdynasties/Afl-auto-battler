## Textures (hand-made, procedural in tools/shade.py; no photo pixels)
Every big surface carries hand-made detail: concrete panels with joints, mottled weathering, aggregate speckle and rain runs under ledges; membrane seams, welded laps, seam grime and dust drifts; steel sheet seams, purlins, faded sheets, scuffs and grime toward sheet bottoms; seats as rows, backs, gaps and concrete aisle steps; Hill turf wear; brick bond; banded stone courses; scoreboard panels faded unevenly.

Pass rule (director, relayed by the stadium lead 2026-11-19): a texture passes when it looks like its photo crop; the stddev is information only. Dark concrete copies the photo's weathering (director's answer here: "Yes, use A").

Each surface beside its photo crop, far (game distance) and near: proof/texture_board.jpg.

Grey stddev (0-255) of each material's base colour, measured unlit on a 24 m wall (far) and a 4 m patch (near), tools/texprobe.py + tools/texstat.py. Before = the old shader on the same colours.

| Material (model colour) | Before far / near | Now far / near | Photo crop sd |
| --- | --- | --- | --- |
| brick | 7.6 / 11.3 | 10.7 / 13.5 | 26.2 |
| brick_red | 19.1 / 28.2 | 20.1 / 28.9 | 26.2 |
| concrete_cream | 4.1 / 4.3 | 15.7 / 18.4 | 11.6 (west stand concrete) |
| concrete_dark | 1.3 / 1.4 | 4.7 / 5.5 | 11.6 (west stand concrete) |
| concrete_grey | 2.9 / 3.1 | 11.2 / 13.2 | 11.6 (west stand concrete) |
| concrete_mid | 1.9 / 2.0 | 7.2 / 8.5 | 11.6 (west stand concrete) |
| concrete_slate | 1.5 / 1.6 | 5.7 / 6.8 | 11.6 (west stand concrete) |
| copper | 11.2 / 14.2 | 11.2 / 14.2 | - |
| glass | 22.8 / 24.7 | 22.8 / 24.7 | - |
| hill_turf | 1.3 / 1.3 | 10.4 / 10.0 | 16.7 (Hill grass) |
| membrane | 2.8 / 2.4 | 10.9 / 10.1 | 45.2 (west stand roof underside) |
| scoreboard | 3.8 / 4.8 | 10.9 / 12.8 | 7.1 (heritage scoreboard) |
| seats_maroon | 26.2 / 23.9 | 29.6 / 28.6 | 31.2 |
| seats_navy | 37.7 / 35.9 | 39.6 / 38.5 | 31.2 |
| seats_red | 16.4 / 13.6 | 22.4 / 21.9 | 31.2 |
| seats_slate | 15.2 / 12.4 | 21.4 / 21.3 | 31.2 |
| seats_teal | 12.7 / 10.0 | 20.0 / 20.4 | 31.2 |
| steel_grey | 8.3 / 7.6 | 9.7 / 8.5 | 2.2 (pale fascia) |
| steel_pale | 9.8 / 8.9 | 11.4 / 9.9 | 2.2 (pale fascia) |
| steel_white | 11.7 / 10.7 | 13.7 / 11.9 | 2.2 (pale fascia) |
| stone | 4.9 / 5.5 | 8.5 / 8.7 | - |

Grey stddev scales with brightness: dark concrete (mean 53) at sd 4.7 varies about as much, relative to its own colour, as cream concrete (mean 212) at 15.7.
