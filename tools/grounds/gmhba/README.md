# GMHBA Stadium (Kardinia Park) exterior model

`gmhba.glb` is the exterior that passed the gate at commit ff1fdabab (md5 2a5040de694f1afe4bf9c26f0d14db3e), with the Joel Selwood Stand (JSS) roof rebuilt on top of it (below).

- Exterior build scripts: `src/` (from .claude/review/gmhba/build at ff1fdabab; renamed from build/, which the repo .gitignore excludes).
- Exterior gate notes: `READY.md`, `proof/topdown/players_roof_bays.txt`.

## Joel Selwood Stand roof

Built from the exterior above by `jss_roof/build_jss.py` (Blender 5.2):

    blender -b --python jss_roof/build_jss.py -- <exterior 2a5040de>.glb gmhba.glb <abs path to jss_roof/>

The old smooth draped sheet is replaced with folded plates copied from the Populous photos, Fabritecture drone photos and the aerial.
- Straight west edge: 8 raised peaks at a 12.2 m pitch, each on a white raking tube with V-struts from the valley feet.
- North-west diagonal and curve: folded plates with a straight outer edge and no peaks (dusk aerial and daylight drone views).
- Light soffit, dark-grey cladding above the white fin band, and a set-back upper wall.

The textures are hand-made by `jss_roof/mktex.py`; there are no photo pixels. There is no crowd.

| Part | Measured (source) | Model |
| --- | --- | --- |
| Rear edge in plan | 97.6 m straight + 20.0 m + 29.4 m diagonal + 6.1 m corner + 5.2 m south = 158.3 m (aerial g19, 0.235 m/px) | 158.3 m |
| Peaks on the straight edge | 8 at 12.2 m, 8 x 12.2 = 97.6 m (aerial g19, S5_014 elevation) | 8 at 12.2 m |
| Overhang past the facade | 5.2 m (Facade_011 close-up) | 5.2 m |
| North-west fold depth | being measured from three views (p09, p20, Street View north) | not final |
