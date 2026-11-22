# ENGIE Stadium (Sydney Showground Stadium) ground model

Rebuilt from scratch to the MCG standard (docs/MCG_STANDARD.md), 2026-11-22. Replaces the one-photo trace.

    cd tools/grounds/engie/model
    python3 osm.py [map.xml]      # OSM -> engie.json: light masts, video wall, site outline (ODbL)
    # plan rings and roof heights: measured from Google Earth, see ../fit/README.md (fit.py 6, tojson.py)
    python3 paint.py              # procedural textures -> tex/ (not committed; rebuilt here)
    python3 proofs.py OUT glb     # with the bpy module (pip bpy 5.2.4): OUT/engie.glb + seat files
    python3 proofs.py OUT plan    # top-down orthographic proof, 520 m square, north up
    python3 proofs.py OUT views ../qa/views.json [names]   # renders from the Google Earth QA cameras

Copy OUT/* to assets/grounds/engie/, run `godot --headless --import`, then
`godot --headless --path . --script tools/grounds/seat_check.gd -- engie` (23,856 seats, 0 failing, on 2026-11-22).

What is modelled: one bowl of stepped rows (lower tier, the level 3 suites' glazed front under the upper
tier's fascia, upper tier; one tier at the open north-east end), aisle stairs with handrails, vomitories, the
players' race; five 1998 roof segments arched between the light towers and hung on cable stays from them, the
2012 north and east roofs with A-frame trusses; eight red triangular lattice towers with V heads, mesh screens,
44 LED floods each, catwalks and ladders; the outside walls of each era; the gap blocks the towers stand on;
the oval video screen on its lattice cage over a charcoal building; 23,856 tip-up seats (official capacity 24,000) (red, the odd orange;
orange at the open end) on black shells.

Sources: a Google Earth top-down trace and stereo heights for the plan and roofs (fit/, measuring only);
OpenStreetMap (ODbL, (c) OpenStreetMap contributors) for the masts, screen and site; the Sydney Showground fact sheet
and ANCR's 2012 project sheet for the suites level, tower count and roof-edge floods; Google Earth 3D and a
Street View photo sphere in the stands for looking at (QA images stay out of the repo).

## The surroundings

    cd tools/grounds/engie/surrounds
    python3 surrounds.py OSM_DIR/*.osm            # -> assets/grounds/engie/surrounds.webp (2 km ground map) + trees.bin
    python3 landmarks.py OSM_DIR OUT/engie_part2.glb   # with the bpy module: the buildings, copied to assets/grounds/engie/

Every building within 1.1 km stands on its own OpenStreetMap footprint at its own height, with the roof form
Google Earth shows: Stadium Australia (the bowl, the ring roof and its two arched trusses, the spiral ramp towers),
Qudos Bank (Afterpay) Arena with its leaning masts, The Dome, the exhibition halls' tent bays and fabric canopy,
the showground pavilions (cross gables; Downes, Munro and Pig & Goat as the long ventilated sheds), Woodchop
Stadium, Schmidt Arena's dirt ring and green-roofed stand, the white marquee, the Brickpit Ring Walk, and the
offices and hotels of Olympic Park. Map data (c) OpenStreetMap contributors, ODbL. Google Earth for looking at only.
