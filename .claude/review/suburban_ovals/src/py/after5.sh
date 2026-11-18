B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
for k in t1_council t2_banks t3_minor t4_country t5_hub t6_north; do t=${k%%_*}; rm -rf out/$t/proof
  "$B" -b -P py/build.py -- spec/$k.json out/$t 2>&1 | grep BUILT
  "$B" -b out/$t/oval_$k.blend -P py/render.py -- spec/${t}_job_proof.json 2>&1 | grep RENDERED
  cp out/$t/oval_$k.glb gd/ovals/
  python py/enc.py out/$t/proof/turntable_frames out/$t/proof/turntable.mp4 2>/dev/null; echo ENC $t
  if [ -f spec/${t}_job_match.json ]; then "$B" -b out/$t/oval_$k.blend -P py/render.py -- spec/${t}_job_match.json 2>&1 | grep RENDERED
    python py/board.py $k out/$t/r/match.png out/$t/board_nofield.jpg; fi
  if [ -f grid/${k}_2000.png ] && [ ! -f spec/${t}_job_match.json ]; then
    python py/side.py grid/${k}_2000.png out/$t/proof/facade.png out/$t/board_side.jpg "model (generic type build, not camera-matched)"; fi
done
echo ALLDONE
