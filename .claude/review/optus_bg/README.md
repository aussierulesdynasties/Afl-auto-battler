# Optus Stadium background scene (row 202 2b)

The 3 x 3 km Blender background around Optus Stadium, Perth. The stadium GLB is the builder's model (md5 5f441917e7aa569f19e47c8f6c1f58c2), and it is used here unedited.

- `pipeline/`: prep.py (OSM + land use, clsfy.py ground classes, fc_overlay.py forecourt ribbons traced from the aerial, surf.py roads/water meshes), build.sh, scene.py, render.py, video_mcg.sh.
- `pipeline/tex/`: hand-made textures. The aerial tiles are reference only and are not committed.
- `frames/`: every 30th frame of the 240-frame orbit (mp4 md5 011a0bbd2bf737b40764b06f9a7acc9b).

Run: `python -E -P prep.py spec/optus.json`, then `bash build.sh optus`, then `bash video_mcg.sh optus`.

Known gaps: there is no one-by-one ribbon count against the aerial, the thinnest ribbons are soft, and the plaza tree planters are not modelled.
