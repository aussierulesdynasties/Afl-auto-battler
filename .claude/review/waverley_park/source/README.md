# Waverley Park (1990-99) build, row 202 step 2b

Python + Blender 5.2 + Godot 4.7 chain that makes `../waverley_park.glb` (this folder: source/) and the proofs beside it.
Run from this folder (Git Bash), with B = blender.exe and G = Godot console exe:

    python maketex2.py && python mktex3.py && python seattex.py && python turf.py   # hand-made textures -> tex2/
    python mktex4.py                                # photo-matched shade variants (re-runs mktex3 first, safe to repeat)
    python gen.py                                   # geometry in metres -> mesh.npz, mats.json
    WAV_CYCLES=1 "$B" -b --python build2.py -- "$PWD/out" render    # matched-camera render (camr6.json)
    python ov2.py && python cmp.py && python proofs.py              # photo | render | overlay, crop boards
    CLOSE="$(cat close.txt)" WAV_CYCLES=1 "$B" -b --python build2.py -- "$PWD/out" close   # facade close-ups
    "$B" -b --python build2.py -- "$PWD/out" export                 # out/waverley_park.glb
    "$G" --path "$PWD/proj" --windowed --script "$PWD/turntable.gd" -- "$PWD/out/waverley_park.glb" "$PWD/out/tt" 4 22

- ref.jpg: the reference aerial (Austadiums waverley-park-5, 1996), used only for the camera fit and overlay; no photo pixels on the model.
- fence.py: the oval's boundary parameterisation P(s, d, z) (perimeter 520.4 m).
- Left out per director rulings of 2026-11-18: the playing field, goal and behind posts, ground boards, all lettering.
- gcrop.py, pj.py, lines.py, dinline.py: measuring helpers (crops, projection, roof-edge d-lines) for checking the model against ref.jpg.
