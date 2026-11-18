B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
for k in t1_council t4_country; do t=${k%%_*}; rm -rf out/$t/proof
  "$B" -b -P py/build.py -- spec/$k.json out/$t 2>&1 | grep BUILT
  "$B" -b out/$t/oval_$k.blend -P py/render.py -- spec/${t}_job_proof.json 2>&1 | grep RENDERED
  cp out/$t/oval_$k.glb gd/ovals/
  python py/enc.py out/$t/proof/turntable_frames out/$t/proof/turntable.mp4 2>/dev/null; echo ENC $t
  "$B" -b out/$t/oval_$k.blend -P py/render.py -- spec/${t}_job_match.json 2>&1 | grep RENDERED
  python py/board.py $k out/$t/r/match.png out/$t/board_nosp.jpg; done
echo ALLDONE
