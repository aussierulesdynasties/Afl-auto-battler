# Grounds pre-inspection (machine pass, 2026-11-21)

_Not the director's fault list and not his review. This is an agent's pass over every ground that plays
in a match, done before he flies through them, so obvious faults are fixed or named first. Looks are his
call; only faults a measurement or a plain picture shows are listed here._

## How it was checked

- **All 30 grounds on main** (`GroundModels.GROUNDS`), each built exactly as a match builds it (Oval3D,
  with the crowd where the ground has seat files). Grounds not yet in the match (Adelaide Oval, Gabba,
  Accor, Mars, Marrara, Traeger, Victoria Park) were not checked.
- **15 fixed cameras per ground**: overhead, both wings, both ends, both goal squares at ground level,
  two from outside the stadium, and six at the fence 2 m up looking out at the stands.
  Contact sheets: project files `preinspection/sheets/<ground>.jpg`.
- **Measured** on the built ground (`tools/visual/preinspect_grounds.gd`): anything of the model standing
  inside the boundary (rays down on a 1.5 m grid, finer on the goal lines), where the model's fence runs
  against the match's fence (a level ray every degree), holes to the void just past the fence, and seats
  with nothing under them, something through them, or inside the boundary.
- Close looks at each flagged spot (`tools/visual/preinspect_look.gd`). Close-ups: project files
  `preinspection/closeups/`.

## Fixed (PR #1950)

| Ground | Fault | Fix |
|---|---|---|
| Bellerive Oval | The ground was laid off its own fence: the south-west stand stood up to 20 m inside the boundary, a light tower stood on the ground, and the east goalposts stood in the front rows of seats. | Laid on the fence the game draws. Nothing of the model is inside the boundary now (was 1,146 grid hits). |
| Windy Hill | Turned 6 degrees off its fence: the fence wall ran up to 6 m inside the boundary on both wings. | Laid on its fence; no hits inside the boundary (was 92). |
| Barossa, Blacktown, Cazaly's, Hands, Mac Point, Riverway, Sky, York Park | From the field the seats were invisible: only their pedestals showed, because each seat shell is one open sheet facing away from Godot's front face. | Open-sheet seats draw both sides. The MCG, Optus and SCG seats are solid and unchanged. |

| GMHBA, ENGIE, Ikon Park, SCG, WACA, Whitten, Manuka, Subiaco, North Hobart, Windy Hill, Norwood, Bellerive | A white strip of sky at the foot of the fence wall: where the model's fence runs 1-4 m outside the match's, nothing was drawn between the turf's edge and the wall, so the empty world under the ground showed through. | A ring of the turf's apron lies just under every model's own ground, from the fence to 8 m past it, painted as the turf is (weather and time of day included). Where the model has ground, the model's shows. |

Captures: `preinspection/closeups/fixed_*.jpg`.

## Open faults (not fixed here)

1. **WACA: the scoreboard stands on the ground.** Its legs are about 5 m inside the boundary, between the
   east goal and behind posts, and the board is 20 m tall. The scoreboard shares its pieces with the rest of
   the model, so moving it is a model edit, not a lay-out fix. (`open_mcg_toprow_scg_pocket_waca_board.jpg`)
2. ~~**MCG: the top row of the top tier has no floor.**~~ Fixed 2026-11-21 (MCG review): the seat file
   carried rows past the back of the south (Great Southern) stand's top tier, up to 15 m of seats in the
   air. 4,568 seats with no floor under them were taken out of `seats_seat_navy.bin` and
   `seats_seat_moss.bin` (73,436 to 68,868). From the field the stand still reads full. Left: about 130
   seats (of 4,050 checked) that sit 1-3 m above the floor the rays find, mostly under the upper tiers'
   overhang on the east side, where they cannot be seen.
3. **SCG: a row of seats in the north-west pocket sits about 1.5 m inside the boundary**, on the apron in
   front of the stand (about 400 seats).
4. **Norwood: both wing stands stand up to 8-9 m inside the boundary.** Norwood's fence is a rounded
   rectangle; the lay-out fits an ellipse, so the wings bulge in while the pockets fall away. An ellipse
   cannot fix it; it needs a fit that keeps every stand outside the fence. (`topdown_fence_*.jpg`)
5. **Smaller fence misses (1-2 m)**: on parts of the lap the model's fence wall runs 1-2 m inside the match's
   fence, leaving a strip of match turf behind the wall: Marvel (both ends), GMHBA, ENGIE, Subiaco,
   People First, Ikon Park, Whitten, Bruce (east end), Manuka, Riverway, North Hobart. Hard to see from
   the field; worth a glance at the fence in the fly-through.
6. **19 of 30 grounds have no seat files, so their stands are empty in a match**: Bellerive, Bruce, ENGIE,
   Football Park, GMHBA, Ikon Park, Jiangwan, Manuka, Marvel, Moorabbin, North Hobart, Norwood,
   People First, Subiaco, Summit, WACA, Waverley Park, Whitten, Windy Hill. (Known: the crowd plan seats
   the crowd ground by ground.)

## For the director's eye (measured, but his call)

- ~~**Roof undersides read as bright grass green**~~ The director chose "grey, a faint green tint"
  (2026-11-21); done in `oval3d_stand.gdshader` for every ground model. Was: at every roofed ground (MCG, SCG, GMHBA, ENGIE,
  People First, Bellerive and others). Rule 2.80 makes the lower half of the sky light the grass bounce,
  and the metal roofs mirror it. Physically there is some green bounce; this much may or may not be what
  he wants. (`open_green_roof_underside_mcg.jpg`)
- **How far each model is stretched to meet the match's fence** (along x across): North Hobart 1.13 x 1.21,
  Windy Hill 1.18 x 1.08, Jiangwan 1.10 x 1.17, Norwood 1.04 x 1.15, Sky 1.13 x 1.15, Bruce 0.88 x 1.14
  (squeezed along and stretched across, 29% apart), GMHBA 0.98 x 1.11, Barossa 1.08 x 1.11, WACA
  0.90 x 1.03. Stands and seats are stretched by the same amounts.

## Checked and clear

Apart from the fence-foot strip above, no holes to the void near the field; no model goalposts doubling the match's; no seats
inside the boundary except the SCG pocket; Optus, Moorabbin, Football Park, Waverley Park, York Park and
the seven kit grounds meet the fence within 0.1 m.

**Not checked:** z-fighting and flicker (still frames do not show it reliably), texture stretching up
close, and anything only visible while moving. Those are for the fly-through.

## Run it again

```
VK_ICD_FILENAMES=/opt/lavapipe/lvp_icd.json xvfb-run -a -s "-screen 0 1280x720x24" \
  godot --path . --rendering-method mobile --script tools/visual/preinspect_grounds.gd -- OUTDIR 960 540 [ground ...]
```

`PREINSPECT_NO_SHOTS=1` measures only (about 10 s a ground headless). One spot close:
`tools/visual/preinspect_look.gd -- OUTDIR <slug> name:px,py,pz,tx,ty,tz[,fov]` (`PREINSPECT_NO_CROWD=1`
hides the crowd).
