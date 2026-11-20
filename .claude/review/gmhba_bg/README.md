# GMHBA Stadium background scene (row 202 2b)

This is the 3 x 3 km scene outside the fence of the GMHBA (Kardinia Park) ground model.
The texture session passed it on 2026-11-20.

- Orbit: `proof/gmhba_orbit.mp4` (md5 ec22c456fecbb06cc156a9b28ebe8882). Every 30th frame is in `proof/frames/`; `proof/ring_sheet.jpg` is the review sheet.
- Stadium model it was built around: gmhba.glb, md5 cd2f83549874b433833b49d0507d161a (texture session repaint).
- No crowd and no nets. Every texture is hand-made (`pipeline/tex`, made by `pipeline/py_mk_*.py`). Aerials were used only as reference, for traced layouts and median colours.
- The scene file it builds (`scene_bg.glb`) is 329 MB, which is over GitHub's 100 MB limit, so it is not in the repo. Rebuild it with `bash build.sh gmhba`, then `bash video_gmhba.sh`. You need Blender 5.2, Python 3.14 and the fetched OSM and aerial data (`fetch.py`, `fetch_parking.py`, `sat_fetch.py` write it to `data/gmhba`). The scripts point at the scratchpad path where they were written, so edit `cd` in `build.sh` and `video_gmhba.sh` first.
- Open: 1 of the 3 photo-matched cameras is fitted (Moorabool, 12 px rms). Far towers more than about 1 km away come out at under 2 px per floor.

## Orbit 20 changes (plan-session fail of orbit 16)
- Shed roofs: hand-made 12 m sheet tile (ribs, seams, skylight sheet, end laps, rust streaks), `py_mk_shed2.py`.
- Shed walls: 12 x 12 m cladding tile with panel seams, roller door, personnel door, downpipes and plinth.
- Car parks: 16 m bay rows, 6 m aisles, pale bay lines (`py_mk_bays.py`, `prep.py` lots modulation).
- Hip roofs: each roof plane shaded by its facing.
- Horizon: km-scale suburb tile (`py_mk_suburb_macro.py`) over the far suburb; farmland past 5 km has paddock colours and fence lines (`py_mk_far_land.py`).
