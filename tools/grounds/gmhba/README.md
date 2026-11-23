# GMHBA Stadium (Kardinia Park) exterior model

`gmhba.glb` is the exterior that passed the gate at commit ff1fdabab (md5 2a5040de694f1afe4bf9c26f0d14db3e), with the Joel Selwood Stand (JSS) roof rebuilt on top of it (below).

- Exterior build scripts: `src/` (from .claude/review/gmhba/build at ff1fdabab; renamed from build/, which the repo .gitignore excludes).
- Exterior gate notes: `READY.md`, `proof/topdown/players_roof_bays.txt`.

## Joel Selwood Stand roof

Built from the exterior above by `jss_roof/build_jss.py` (Blender 5.2):

    blender -b --python jss_roof/build_jss.py -- <exterior 2a5040de>.glb gmhba.glb <abs path to jss_roof/>

The roof copies the Esri aerial and the Google Earth 3D view (camera solved from the four tower tops/bases and the cats sign: rms 4.43 px, max 6.27 px at 1280 wide; held-out points 11.8 and 8.4 px).
- Outer zone: low folded plates whose fold lines meet the west edge at the aerial dots; behind the block it is a flat sliver (no folds, as in the aerial).
- Zigzag step: the inner folded plates stand up along a 6-ridge zigzag, 2 ridges behind the block.
- Eave slopes from 16.4 m (south) to 14.0 m (north), measured by back-projecting the GE eave; silver-white roof, dark glass under the eave.

The textures are hand-made by `jss_roof/mktex.py`; there are no photo pixels. There is no crowd.

| Part | Measured (source) | Model |
| --- | --- | --- |
| Inner zigzag ridges | 6, 2 behind the block (aerial) | 6, 2 |
| Outer fold apexes on the west edge | y 71.6 / 57.5 / 45.3 m, then 12.2 m pitch (aerial) | same |
| Outer ridge rise | 1-2 m (GE elevation readout) | 2.0 m |
| Inner step | about 4 m (GE readout); 5.8 m from 3.5 m shadows; the wide view cannot separate them (both rms about 5 px) | 4.0 m |
| Eave height | 13.96 / 15.17 / 16.39 m at y 78 / 40 / 2.4 (GE wide back-projected; ground check -0.95 m) | 16.4 - 0.0315 (y - 2.4) |

Known, not in this roof: the cats block (from the passed exterior) sits about 3 m south of the aerial.
