# GMHBA Stadium background scene (row 202 2b)

This is the 3 x 3 km scene outside the fence of the GMHBA (Kardinia Park) ground model.
The texture session passed it on 2026-11-20.

- Orbit: `proof/gmhba_orbit.mp4` (md5 3ade3ef95b1853c959de516200163a90). Every 30th frame is in `proof/frames/`; `proof/ring_sheet.jpg` and `proof/topbands.png` are the review sheets.
- Stadium model it was built around: gmhba.glb, md5 2a5040de694f1afe4bf9c26f0d14db3e.
- No crowd and no nets. Every texture is hand-made (`pipeline/tex`, made by `pipeline/py_mk_*.py`). Aerials were used only as reference, for traced layouts and median colours.
- The scene file it builds (`scene_bg.glb`) is 329 MB, which is over GitHub's 100 MB limit, so it is not in the repo. Rebuild it with `bash build.sh gmhba`, then `bash video_gmhba.sh`. You need Blender 5.2, Python 3.14 and the fetched OSM and aerial data (`fetch.py`, `fetch_parking.py`, `sat_fetch.py` write it to `data/gmhba`). The scripts point at the scratchpad path where they were written, so edit `cd` in `build.sh` and `video_gmhba.sh` first.
- Open: 1 of the 3 photo-matched cameras is fitted (Moorabool, 12 px rms). Far towers more than about 1 km away come out at under 2 px per floor.
