# ENGIE Stadium (Sydney Showground Stadium) ground model

Rebuilt from scratch to the MCG standard (docs/MCG_STANDARD.md), 2026-11-22. Replaces the one-photo trace.

    cd tools/grounds/engie/model
    python3 osm.py [map.xml]      # OSM -> engie.json: roof front/back edges, light masts, video wall (ODbL)
    python3 paint.py              # procedural textures -> tex/ (not committed; rebuilt here)
    python3 proofs.py OUT glb     # with the bpy module (pip bpy 5.2.4): OUT/engie.glb + seat files
    python3 proofs.py OUT plan    # top-down orthographic proof, 520 m square, north up
    python3 proofs.py OUT views ../qa/views.json [names]   # renders from the Google Earth QA cameras

Copy OUT/* to assets/grounds/engie/, run `godot --headless --import`, then
`godot --headless --path . --script tools/grounds/seat_check.gd -- engie` (0 failing seats on 2026-11-22).

What is modelled: one bowl of stepped rows (lower tier, the level 3 suites' glazed front under the upper
tier's fascia, upper tier; one tier at the open north-east end), aisle stairs with handrails, vomitories, the
players' race; five 1998 roof segments arched between the light towers and hung on cable stays from them, the
2012 north and east roofs with A-frame trusses; eight red triangular lattice towers with V heads, mesh screens,
44 LED floods each, catwalks and ladders; the outside walls of each era; the gap blocks the towers stand on;
the oval video screen on its lattice cage over a charcoal building; 19,031 tip-up seats (red, the odd orange;
orange at the open end) on black shells.

Sources: OpenStreetMap (ODbL, (c) OpenStreetMap contributors) for the plan; the Sydney Showground fact sheet
and ANCR's 2012 project sheet for the suites level, tower count and roof-edge floods; Google Earth 3D and a
Street View photo sphere in the stands for looking at (QA images stay out of the repo).
