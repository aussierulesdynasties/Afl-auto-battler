# Brighton Homes Arena (Springfield QLD), exterior model: proof set

Row 202 step 2b. Stadium only: stands, roofs, towers, scoreboard, the oval fence, buildings, and the ground from the oval fence out.
Left out on instruction: the playing field (director 2026-11-18: "Leave field out"; the game draws its own grass inside the fence), pool, court, ground mural, trees, background.
Also left out, per the secretary's finish list of 2026-11-18: goal and behind posts, and all lettering (the BRIGHTON HOMES ARENA sign on the indoor centre). No sponsor boards; no nets.

## The model
- `brightonhomes_exterior.glb`: 68 MB, 101,217 triangles, 200 meshes, 50 materials.
- Units are metres. In Blender, x is east, y is north and z is up; the glTF file stores +Y up.
- Origin: lat -27.672166, lon 152.904245 (the OSM origin). The oval centre sits at (2, -2).
- Every material is double-sided and has a hand-made colour, roughness and normal texture (procedural, no photo pixels).
- `mesh_dark` is alpha-blended.
- Roof solar panels are included (lead's ruling 2026-11-18: the Esri overhead is a real photo of the roof; the side photos cannot see it).
- Tints are baked into the colour textures, so the GLB looks the same in any viewer.
- The turntable stills, mp4 and facade close-up are rendered from the exported GLB re-imported, not from the source scene.

## Files
- `overlays/<view>_board.png`: 1920x1080 2x2 board (photo | render | 50% blend | model edges in red on the photo).
- `overlays/<view>_blend50.png`: full-size 50% blend.
- Views:
  - `main_aerial`: 2023 drone, WNW sun
  - `n68`: 2023 aerial from the south
  - `ex3`: Angus Martin's Exterior3 frontal of the west stand, sun az 103 el 20
- `parts/*.png`: crop boards, with the photo crop above the render crop from the same fitted camera.
- `turntable_045/135/225/315.png`: 1920x1080. The name is the camera bearing from the ground centre (degrees clockwise from north).
- `turntable.mp4`: 72-frame orbit, 5 degrees per frame, 12 fps, 1280x720.
- `facade_closeup.png`: west stand front at 26 m, ex3 sun.

## Differences from the photos still open
- **Lion on the copper screen.** It reads faint in the render; in the photo it is a bright gold lion.
- **West stand seats** are flat rows, not individual chairs. The doors are solid black, not grilles.
- **Missing details:** the speakers hanging in front of the glass, and detail on the roof soffit.
- **ex3 flags** render as dark shapes from the front. The photo shows coloured flags. From the main aerial the textured flag faces show.
- **South of the west stand:** a possible south ramp below y -22.3 is suggested by Esri but not shown in any photo, so it is not modelled.

## Build source (`build/`)
Everything needed to rebuild the GLB and the proofs, run from inside `build/` with Blender 5.2:
- `blender -b --python bl_build.py -- <abs build dir> <abs>/m2.blend <abs>/t_main.png 64` assembles the model from the `*_parts.json` / `ground_site.json` inputs and the hand-made textures in `tex/` (made by `texgen.py`, `sign.py`).
- `blender -b m2.blend --python bl_export.py -- out.glb` writes the GLB.
- `nofield.sh` runs the whole chain (build, photo-camera renders, export, turntable stills, facade, frames, mp4). Photo references are not committed; `board.py` / `crops.py` need them.
- Geometry generators (geom.py, patch*.py, ws*.py, ramp.py, site_trim.py) are included for reference; their raw OSM/Esri inputs are not.
