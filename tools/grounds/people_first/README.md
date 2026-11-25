# People First Stadium (Carrara) to the MCG standard

Row 202 2b. The ground the director passed (#1853, #1860, #1889) rebuilt from its own source to the MCG standard
(docs/MCG_STANDARD.md): checked against Google Earth 3D from the same cameras, details modelled and never painted on,
and the ground set in its surroundings. Looks only: nothing here reads back into play.

## Pipeline

    tools/grounds/people_first/src/build.sh /tmp/pf.glb          # Blender 5.2, or pip bpy 5.2.4 (no render)
    node tools/grounds/fit_fence/split.mjs /tmp/pf.glb assets/grounds/people_first/people_first   # two pieces under 45 MB
    python3 tools/grounds/people_first/surrounds.py                 # surrounds.webp, trees.bin, buildings.bin
    godot --headless --path . --import --quit                       # then `git checkout assets/grounds/mcg` (import rewrites its webps)

- `src/build.py` is the passed build (`.claude/review/peoplefirst/build/build5.py`, r35) plus r36. `build.sh` holds the
  options that reproduce the passed model vertex for vertex (`EVEN=1 NEARDZ=3 MEMB=0.27` were missing from the old README).
  Its hand-made textures stay in `.claude/review/peoplefirst/build/htex` (no photo pixels).
- `src/precinct.json`: 24 sheds, halls, marquees and portables round the ground, plan and roof colour read off the
  reference satellite (kept in the project files, never committed; surrounds.py reads it from PF_SAT), heights from Google Earth.
- `measure/roof_edge_fit.py` (r38, 2026-11-23): measures the roof's outer edge on the reference satellite and fits one
  construction to it: 38 ribs at the measured valleys (regular along the outline, valleys a median 1.1 m off the fit), a
  smooth valley-radius curve (median 0.24 m off), a lobe depth of 3.5-4.0 m (median 0.21 m off), lobes
  `r = V + depth*sin(pi*t)^1.35`, and a smooth inner line. Writes `src/ribfit.json`; `build.sh` reads it (`RIBFIT`).
  `measure/edge_check.py` scores an outline against the satellite's edges: r37 had 78% of the roof edge within 2 m
  (its scallops were 2 m deep against the real 4 m, on 40 even ribs against 38 real ones); r38 has 95% within 2 m,
  88% within 1 m. Board: project files `people-first-rebuild/r38_roof_outline_plan.jpg`.
- `qa/`: `ge_compare.py` and `ge_shoot.js` (copies of GMHBA's, with People First added), `views.json` (13 wide views)
  and `close.json` (12 close-ups). See the docstring for the four commands.

## r36 (2026-11-22): what Google Earth showed and what changed

| Google Earth | Before | Now |
| --- | --- | --- |
| Outer wall: near-black panels behind vertical ribs, all round behind the yellow columns | Royal-blue textured wall | Charcoal wall with modelled fins, 1.0 m apart, 0.5 m deep |
| Podium: copper-brown vertical blades in two tones over a dark wall | Painted multi-colour stripes | Modelled bronze fins, 0.7 m apart, 0.45 m out |
| Podium roof: pale grey folded tent, ridges from the corners | Flat white roof | Tent roof rising 4.5 m to the middle, dark parapet |
| Scoreboard: screen in a steel lattice 3 m deep, standing on the ground | Navy box on two white legs and posts | Screen on a lattice frame: posts, horizontals, crossed diagonals |
| Entry pods round the foot, a pair with drums at the south entry | None | 14 x 9 x 6.5 m pods with a recessed window band |
| Roof's navy band: glazed panels in white frames | One white bar per bay | Four bars per bay |
| Seats: brick red | Bright orange-red (242,92,74) | 206,66,58 |
| Precinct: bitumen ring, sheds and halls, the Nerang River lined with bush, the training ovals | Nothing round the model | OpenStreetMap map, river (relation stitched whole), 3,700 trees, 24 precinct buildings, street houses |

## Known gaps

- The Gold Coast skyline (Surfers Paradise) on the eastern horizon is not drawn.
- Google Earth's upper tier reads near-black under the roof; ours is lit brighter (the renderer's shade, not the seat colour).
- Street View has no photo sphere on the ground, so the inside is judged from Google Earth's bowl views.
- Close-up Google Earth views come out wider than ours from the same numbers; judge those by eye.
