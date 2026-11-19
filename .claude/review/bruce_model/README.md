# Bruce Stadium exterior (row 202 step 2b)

Reference: ref46.jpg = NAA A6135 K18/4/90/46 (April 1990); ref50.jpg is the second camera. Model: bruce3.glb.
All textures in tex/ are hand-made (procedural, paint.py); no photo pixels.
Rulings applied: stadium only, no field, no posts, no boards, no lettering, cut + turnstiles.

Rebuild, from this folder:
1. `python paint.py`: writes tex/*.png and tex/index.json.
2. `python gen2.py`: writes parts.json.
3. `blender -b --python build2.py -- parts.json "$PWD/bruce3.glb" "$PWD/render46.png" "$PWD/render50.png"`.
4. `python proof.py pf`: writes the photo/render/overlay sheet and the boards (needs ref46.jpg).
5. `bash rr.sh`: turntable, close-ups (cameras in g/), mp4, copy to .claude/review (Godot project in tt/).
