B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
for k in t3_minor t6_north; do t=${k%%_*}; rm -rf out/$t/proof; "$B" -b -P py/build.py -- spec/$k.json out/$t 2>&1 | grep BUILT; "$B" -b out/$t/oval_$k.blend -P py/render.py -- spec/${t}_job_proof.json 2>&1 | grep RENDERED; cp out/$t/oval_$k.glb gd/ovals/; python py/enc.py out/$t/proof/turntable_frames out/$t/proof/turntable.mp4; done
for k in t2_banks t4_country; do t=${k%%_*}; rm -f out/$t/proof/turntable_0001-0096.mp4; python -c "
import json; j=json.load(open('spec/${t}_job_proof.json')); j['views']=[v for v in j['views'] if 'video' in v]; json.dump(j,open('spec/${t}_job_v.json','w'))"
  "$B" -b out/$t/oval_$k.blend -P py/render.py -- spec/${t}_job_v.json 2>&1 | grep RENDERED; python py/enc.py out/$t/proof/turntable_frames out/$t/proof/turntable.mp4; done
echo ALLDONE
