# GMHBA Stadium (Kardinia Park) exterior: ready for gate

Model: `model/gmhba.glb` (built 2026-11-19 14:33 Melbourne). Stadium only: no field, posts, nets, lettering,
sponsor boards or temporary stands. Hand-made textures only, no photo pixels.

## Faults fixed this round
- East (Reg Hickey) stand pulled back 11-14 m onto the satellite.
- West roof: leading edge at about 10 m (satellite) and back edge 40-42.7 m.
- Main canopy refit: 22 bays on the satellite gutter gaps, with the zig-zag back edge (a notch and a tip per bay).
- West wall cap now sits under the low canopy only (a < 156).
- North stand back edge (sawtooth) moved to 49-50.5 m.
- NE corner knots set to 30-46 m.
- SE pocket: the stadium stops at the Moorabool St kerb. The jagged OSM outline is replaced by the satellite block
  edge (45 m, 279-285) and a straight run to the kerb, which also fixes a broken wall join.
- SE and NE light-tower heads moved onto the satellite heads, by 3 m and 3.8 m.
- NW stair tower added (99.5-105.5).
- The GMHBA sign is a blank panel with no lettering.

## Top-down (Esri z19, north up, 0.25 m/px, lean corrected y+0.035 z): model edge vs satellite
| Sector (deg from pitch centre) | Result |
|---|---|
| Players Stand roof 204-275 | every notch and tip within 0.03-1.75 m (`proof/topdown/players_roof_bays.txt`) |
| West face 168-200 | about 0.5 m |
| Low SW canopy 131-165 | about 1 m |
| West 110-130 | about 1.5 m |
| NW stair tower 99.5-105.5 | 48.75 vs 47 m (1.75 m) |
| North stand 60-100 | 49.5-50.5 vs 50-51 m (under 1 m) |
| NE corner 20-36 | 1-2 m |
| East -20..20 | 21-23 vs about 22 m (about 1 m) |
| SE roof -100..-82 | zig-zag within about 1 m |
| SE pocket 279-303 | block 45 vs 45 m; kerb within about 1 m |
| Light-tower heads | NW and SW within 2 m; SE and NE moved onto them |

## Proofs
- `proof/topdown/topdown_board.png` (outline on the satellite plus the table), `ol.png`, `top2.png` (raw ortho),
  and `unwrap_*.png` polar unwraps (6 px per degree and per metre; red is the model edge).
- `proof/overlays/ov_p1.png` and `ov_p2.png`: camera-matched renders over photos p1 and p2 (blend on top, edges on
  the photo below).
- `proof/turntable/turntable.mp4` (72 frames, 5 degrees apart, 12 fps), plus four stills.
- `proof/closeups/`: facade close-ups and six join close-ups (NE 36, NW 100, SW box 156, W/Players 209, SE pocket 278,
  E pocket 320), with `joins_sheet.png`.
- `build/`: build and proof scripts.

## Open questions
- SE pocket: the satellite shows a light ribbed structure out to x 28-33. Photo p1 shows a low seat bank and a grey
  multi-level building. The imagery dates may differ. The model follows the satellite plan, with heights from p1.
- SE light-tower head: the direction it faces could not be read with confidence from the satellite.
- Photo p1's camera puts the west canopy about 10 m deeper than the satellite does. Heights were re-solved to keep the
  photo rows; the plan follows the satellite.
