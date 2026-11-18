B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
for k in "$@"; do t=${k%%_*}
  if [ "$t" != t1 ]; then rm -rf out/$t/proof
  "$B" -b -P py/build.py -- spec/$k.json out/$t 2>&1 | grep BUILT
  "$B" -b out/$t/oval_$k.blend -P py/render.py -- spec/${t}_job_proof.json 2>&1 | grep RENDERED
  cp out/$t/oval_$k.glb gd/ovals/
  python py/enc.py out/$t/proof/turntable_frames out/$t/proof/turntable.mp4 2>/dev/null; echo ENC $t
  if [ -f grid/${k}_2000.png ]; then python py/side.py grid/${k}_2000.png out/$t/proof/facade.png out/$t/board_side.jpg "model (generic type build, not camera-matched)"; fi
  fi
  "$B" -b out/$t/oval_$k.blend -P py/render.py -- spec/${t}_job_sb.json 2>&1 | grep RENDERED; echo SB $t
done
echo ALLDONE
