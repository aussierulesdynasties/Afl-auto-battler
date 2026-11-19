# Bellerive Oval (Ninja Stadium) exterior: READY FOR GATE

Row 202 step 2b. Branch `claude/bellerive-exterior`. Model: `bellerive.glb` (x east, y north, z up in Blender; the
glTF export turns it Y-up, so north is glTF -Z). Build: `tools/grounds/bellerive/model/` (`build.py`, `paint.py`,
`bellerive.json`); proofs `model/proofs.py`, `work/proofboard.py`, `work/texboard.py`.

Scope: stadium only, stopping at the outer fence. No turf, posts, nets, temporary stands, ads or crowd.

The model holds:
- the Boon Stand (S);
- the Ponting Stand (W) with its faceted skin and roof skylights;
- the Members / Edwards Pavilion (NW) with the NINJA STADIUM sign tower;
- the Northern Stand;
- the east grass terrace and hill;
- the scoreboard;
- four light towers;
- the fence and apron.

## Proofs
| What | File |
| --- | --- |
| Camera-matched overlays (GE above, model over GE below) | `overlay_f000/f090/f135/f180/f225/f270/f315/i030/i180.jpg` |
| Turntable | `turntable.gif`, `turntable_000…315.jpg` |
| Facade close-ups | `close_facade_boon/ponting/members.jpg` |
| Join close-ups | `close_join_boon_ponting_in/out`, `close_join_ponting_members_in/out`, `close_join_members_end`, `close_join_terrace_boon`, `close_join_nstand` |
| Top-down overlay on the Esri satellite (magenta model edges, cyan outline, 5 m grid) | `topdown_on_satellite.jpg` |
| Each surface: hand-made texture, GE photo crop, model at the same pixels | `textures_vs_photo.jpg` |
| Grey stddev of every texture (all >= 10; lowest conc_grey 10.6) | `stddev.txt` |
| Seating close-ups, empty seats in their real colours | `close_seats_boon.jpg`, `close_seats_ponting.jpg` |
| Ground sign beside its reference crop | `sign_vs_ref.jpg` |

## Top-down fit
Roof and stand edges follow the Esri roofs to within about 2 m (8 px at 4 px/m) all round. The cyan outline runs
wider on the N and E because it includes the apron and the grass hill, which are inside the fence.

Light towers, scoreboard and Northern Stand sit on their satellite positions.

## Faults fixed before push
- Gate 2026-11-19, fault 1: the Ponting wall's navy triangles are gone. The wall now copies GE f270: pale facets over a band of slanted panels in mid-blue (80,113,150), sky blue (117,154,197) and blue-grey (123,141,167), all sampled from the photo.
- Gate 2026-11-19, fault 2: the east hill is now green grass (100,134,80, with dry patches). It falls from the top terrace step down to the hill's outer edge. The flat raised ring is gone, and the terrace has 7 concrete steps. See `overlay_f135.jpg`.
- The Ponting seat blue was too saturated. It now copies the GE sample (56,92,120).
- The sign lacked the cap emblem, and its navy panel ran to the top. Both now match GE x330.
- The facade textures were upside down.
- The north building and the terrace hill were too tall.

no open faults

The lead's folder `trusting-edison-c1068b` was NOT reset (no reset, checkout, stash or clean there).
