# Ground fault scan

A machine pass over a stadium before the director looks at it in the ground inspector, so he stops
finding obvious faults himself. It runs on GitHub's runners (the ground models are private and only
reach CI and the PC): `.github/workflows/fault-scan.yml`, one job a ground.

1. `scan.gd dump` builds the ground exactly as the inspector does (Oval3D's light, turf and posts,
   then `GroundModels.instantiate`: model, seats, legs, surrounds, backdrop) and writes every visible
   mesh in world space: the inspector's coordinates, what its C key copies.
2. `osm.py` reads OpenStreetMap round the ground (Overpass, else the main API), in metres from the
   centre circle (`tools/grounds/terrain/grounds.json`). Data (c) OpenStreetMap contributors, ODbL.
3. `analyse.py` measures (rays through the whole scene with Embree):
   - printed boards read from the front as a person sees them, by OCR both ways round: words that read
     backwards or upside down; textures drawn mirror-image; stretched or squashed textures; two-sided
     signs; sign materials that dim their print;
   - floating pieces (a connected piece with nothing within 12 cm of it and air under it) and posts that
     stop short of the floor;
   - seats: colours mixed at random (share of each seat's neighbours in another colour), tipped, huge,
     facing away, off their treads, with the stand through them, inside the fence; seat legs as huge
     slabs, legs with no seat, legs over the field; seats that see the sky where the seats round them
     are covered (a gap in the roof, fascia or panels);
   - trees on roofs or floating; one tree model copied many times;
   - the model against the real stadium outline (flipped or not, and how far off), the stadium or a
     building standing on a real road or path;
   - real bridges and walkways with no deck, real buildings missing, open shelters built as solid
     blocks, building roofs with crossing or upside-down triangles, jagged outlines;
   - the game's own made-up facades and stock trees, anything standing on the arena.
4. `scan.gd render` films each finding (ringed in red by `report.py`) and a fixed set: the broadcast
   cameras, an aerial orbit, the street all round, the seats (looking at the field and up at the roof),
   and straight-down map tiles.
5. `report.py` writes `<slug>.md` with its JPEGs: the artifact `fault-scan-<slug>`.

What a machine cannot judge (whether a facade is the real one, colours against photos, made-up
detail) is reviewed by eye from the shots before a list goes to a ground's owner. The lists live in
the project files, `fault-scan/<slug>.md`.
