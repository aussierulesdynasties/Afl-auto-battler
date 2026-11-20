# People First Stadium background scene (v9)

A 3x3 km scene around People First Stadium (Carrara), built in Blender from OSM plus Microsoft building footprints. Its textures are hand-made; the aerial is used as reference only.

- Stadium model: `.claude/review/peoplefirst/model/peoplefirst.glb`, md5 `3e5c537fb39be08d9efdaeeb329a5fe5` (PR #1889). It isn't copied here; put it at `ground/peoplefirst.glb` before building.
- Orbit mp4 (not committed): md5 `6dafffcec780a590ab03edb74447dab9`, 240 frames, 1280x720.
- `proof/frames30/`: every 30th orbit frame. `proof/peoplefirst_ring.png`: the ring sheet.
- Gates: the texture session passed it, and so did the plan session.
- Build: `scripts/rebuild_pf.sh` runs prep, bake_ground and `scene.py -- spec/peoplefirst.json`. Then render with `render.py -- job_video.json`.
- Not included: the GLB, scene.blend, and the OSM and footprint caches.
d9c4eab6155bb543c6b456e2615913d3 *.claude/review/peoplefirst_bg/proof/frames30/f_0001.png
46f05b390ed917058dd3955550a2c057 *.claude/review/peoplefirst_bg/proof/frames30/f_0031.png
ed5ae35de70cb353815605fa709f1033 *.claude/review/peoplefirst_bg/proof/frames30/f_0061.png
0478f1424a6500ea0b212b2ed017ec12 *.claude/review/peoplefirst_bg/proof/frames30/f_0091.png
347273644582d3344df701cb7c3ef78e *.claude/review/peoplefirst_bg/proof/frames30/f_0121.png
dba3176ee345c19bf74c7e8ad4ea9544 *.claude/review/peoplefirst_bg/proof/frames30/f_0151.png
e156564f5bc83421dbc9593023833bda *.claude/review/peoplefirst_bg/proof/frames30/f_0181.png
2d0d975b386b28ad6bddb53b2ee991fa *.claude/review/peoplefirst_bg/proof/frames30/f_0211.png
