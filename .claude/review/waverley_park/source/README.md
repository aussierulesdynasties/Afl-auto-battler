# Waverley Park (1990-99) build, row 202 step 2b

Python + Blender 5.2 + Godot 4.7 chain that makes `../waverley_park.glb` (this folder: source/) and the proofs beside it.
Run from this folder (Git Bash), with B = blender.exe and G = Godot console exe:

    python maketex2.py && python mktex3.py && python seattex.py && python turf.py   # hand-made textures -> tex2/
    python mktex4.py                                # photo-matched shade variants (re-runs mktex3 first, safe to repeat)
    python paint_tex.py                             # hand-painted detail on every plain map (texpaint.py), keeps mktex4's mean colour
    python gen.py                                   # geometry in metres -> mesh.npz, mats.json
    WAV_CYCLES=1 "$B" -b --python build2.py -- "$PWD/out" render    # matched-camera render (camr6.json)
    python ov2.py && python cmp.py && python proofs.py              # photo | render | overlay, crop boards
    CLOSE="$(cat close_all.txt)" WAV_CYCLES=1 "$B" -b --python build2.py -- "$PWD/out" close   # facade close-ups + 2 empty-seat views
    WAV_CYCLES=1 "$B" -b --python build2.py -- "$PWD/out" top    # straight-down orthographic render, 0.25 m/px, north up
    python topboard.py sat_esri.jpg                                 # satellite | model | overlay board
    python texboard.py                                              # texture vs photo crop board + stddev list
    "$B" -b --python build2.py -- "$PWD/out" export                 # out/waverley_park.glb (oval centre at origin, north = glTF -Z)
    "$G" --path "$PWD/proj" --windowed --script "$PWD/turntable.gd" -- "$PWD/out/waverley_park.glb" "$PWD/out/tt" 4 22

- ref.jpg: the reference aerial (Austadiums waverley-park-5, 1996), used only for the camera fit and overlay; no photo pixels on the model.
- North and plan check: searched for a 1990s straight-down aerial (web search; Monash Library Flickr album "VFL/AFL Park,
  Mulgrave", 6 photos; Esri Wayback back to 2014). Found one survey aerial, Crown Lands and Survey run of 1 April 1982
  (Flickr monlib/50243306931): 8 years before the era and only a small web image, so not used.
  By the legacy rule the plan is checked against today's
  straight-down imagery for the parts that still stand (the oval and the members' stand). sat_esri.jpg = Esri World
  Imagery export (2026), 500 m square, 0.25 m/px. topfit.py fits the model fence to its oval edge (rigid, no scale):
  north.json holds the turn (4.05 deg) and offset. toplean.py and topwb.py repeat it on Esri Wayback flights
  (2014-2024) to tell a building's lean from a real offset (2024 is visibly oblique; 2018 and 2026 near straight down).
  radial.py / radial2.py read brightness along lines straight out from the fence, satellite vs model.
- fence.py: the oval's boundary parameterisation P(s, d, z) (perimeter 520.4 m).
- Left out per director rulings of 2026-11-18: the playing field, goal and behind posts, ground boards, all lettering.
- gcrop.py, pj.py, lines.py, dinline.py: measuring helpers (crops, projection, roof-edge d-lines) for checking the model against ref.jpg.
