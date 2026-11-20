# GMHBA Stadium: Joel Selwood Stand roof

`gmhba.glb` is the full ground model. Only the Joel Selwood Stand (JSS) roof changed. It is built from model cd2f83549874b433833b49d0507d161a by `jss_roof/build_jss.py` (Blender 5.2):

    blender -b --python jss_roof/build_jss.py -- <cd2f8354 model>.glb gmhba.glb <abs path to jss_roof/>

The old smooth draped sheet (866 faces) is replaced with a roof copied from the Populous photos: the Gate 1 Polly Farmer elevation, the facade close-up and the dusk aerial.
- Flat folded plates run from the front edge to the rear. Each bay has a ridge up to a beak peak and valleys between the peaks.
- The beaks overhang the facade. The rear edge is straight in plan and zigzags in elevation.
- Each peak has a white raking column under it, plus V-struts from each valley foot up to the two neighbouring peaks. The struts land on top of the white fin band.
- Above the fin band is dark grey cladding.
- The plates have white edge trims, steel ribs underneath and matte ribbed sheeting.

The textures are hand-made by `jss_roof/mktex.py`; there are no photo pixels. There is no crowd and nothing else in the model changed.

| Part | Measured (source) | Model |
| --- | --- | --- |
| Rear edge length in plan | 155.7 m (traced on aerial, 0.47 m/px) | 155.7 m |
| Bays and beak peaks | bay about 10-11 m (Gate 1 photo, bay about 1.5 x rise) | 15 bays of 10.38 m |
| Beak rise above the valleys | about 0.65 x bay = 6.8 m (Gate 1 photo) | 7.0 m |
| Beak overhang past the facade | about half a bay = 5.2 m (close-up photo) | 6.0 m |
| Supports per peak | 1 column and 2 V-struts (Gate 1 photo) | 1 column and 2 V-struts |
| Strut feet | top of the white fin band (Gate 1 photo) | top of the fin band, 11 m |
| Join with the west stand | no gap (aerial) | the last valley sheet tucks under the neighbouring roof |
