B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
for k in t2_banks t4_country t6_north; do t=${k%%_*}; rm -rf out/$t/proof
  "$B" -b -P py/build.py -- spec/$k.json out/$t 2>&1 | grep BUILT
  "$B" -b out/$t/oval_$k.blend -P py/render.py -- spec/${t}_job_proof.json 2>&1 | grep RENDERED
  cp out/$t/oval_$k.glb gd/ovals/
  python py/enc.py out/$t/proof/turntable_frames out/$t/proof/turntable.mp4; echo ENC $t; done
"$B" -b out/t4/oval_t4_country.blend -P py/render.py -- spec/t4_job_match.json 2>&1 | grep RENDERED
python py/board.py t4_country out/t4/r/match.png out/t4/board_v5.jpg
echo ALLDONE
