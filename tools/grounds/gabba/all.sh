cd "$(dirname "$0")"
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
"$B" -b -P build.py -- model_in6.json gabba.glb "$PWD/gabba.blend" "$PWD/htex" 2>&1 | grep -E "^TRIS"
( "$B" -b "$PWD/gabba.blend" -P render.py -- camB6.json "$PWD/r6.png" >/dev/null 2>&1; "$B" -b "$PWD/gabba.blend" -P render.py -- camB6.json "$PWD/m6.png" mask >/dev/null 2>&1; CAMFIT=camfit10.json C:/Python314/python.exe compose.py go r6.png m6.png v6.png; "$B" -b "$PWD/gabba.blend" -P render_cy.py -- camB6.json "$PWD/r6cy.png" >/dev/null 2>&1; "$B" -b "$PWD/gabba.blend" -P top.py -- "$PWD/top_s.png" >/dev/null 2>&1; "$B" -b "$PWD/gabba.blend" -P top.py -- "$PWD/top_l.png" -0.117 -0.117 >/dev/null 2>&1; echo BL_DONE ) &
bash rt3.sh
wait; echo ALL_DONE
