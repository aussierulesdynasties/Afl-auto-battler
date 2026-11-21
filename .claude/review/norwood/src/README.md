# Norwood Oval exterior: build scripts

Row 202 step 2b. Model of Norwood Oval (Coopers Stadium) as it stands today, stadium only.
Director rulings applied (2026-11-18): no people, no boards ("C: no boards"), field left out ("Leave field out"),
posts out ("Posts out"), no lettering ("C: no lettering"). The ground's own fence is kept; there are no nets.

Textures are painted by hand in numpy/PIL (tex.py + tex2.py); no photo pixels.

## Layout the scripts expect

    nw/
      main.jpg     reference aerial (April 2024 Gather Round, 1200x675; not committed)
      tex/         written by tex.py
      fit/         these files

## Run (from fit/)

    python tex.py                 # textures -> ../tex + spec.json
    bash runall3.sh               # match render + overlay, turntable stills, close-ups, GLB, 96-frame turntable mp4

runall3.sh calls Blender 5.2 in the background (`blender -b --python build.py -- <cmd> <ABSOLUTE OUT>`).
OUT must be an absolute path. Commands: match, turn, close (VIEWS=a,b renders only those views), glb, turnvid.
geo.py builds every part; the pop list at its end holds the parts the rulings removed.
