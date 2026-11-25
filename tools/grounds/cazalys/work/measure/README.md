# Cazaly's: measuring heights from Google Earth (2026-11-22)

Scripts from the shape-first pass. They run from a scratch WORK dir laid out as `of/` (GE obliques + v.json),
`st/` (three GE top-down views sA/sB/sC + corner observations), `rf/`, `ob/`; GE captures stay out of the repo.

1. `solve2.py v.json NAMES` solves each oblique's camera (position, yaw, pitch, roll; F = 1585.8 px fixed) from the
   painted field lines (boundary line, 50 m arcs, centre square, goal squares) by ICP along the projected line normals.
   Grandstand views solved to 0.4-0.8 px rms. The club views did not solve: the painted goal squares and 50 m arcs are
   not centred on the boundary line's long axis, so the line model needs the measured goal positions first.
2. `zline.py` / `zedge.py` read each roof corner's height on the vertical through its top-down position.
3. `newroof.py` writes the measured roof (outline, plane, tie frames) into roof.json.
4. `tiers.py` / `tri.py` project and triangulate tier lines.
