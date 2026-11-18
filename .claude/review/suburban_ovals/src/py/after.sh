B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
while tasklist //FI "IMAGENAME eq blender.exe" 2>/dev/null | grep -q blender.exe; do sleep 20; done
for k in t3_minor t6_north; do t=${k%%_*}; rm -rf out/$t/proof; "$B" -b -P py/build.py -- spec/$k.json out/$t 2>&1 | grep BUILT; "$B" -b out/$t/oval_$k.blend -P py/render.py -- spec/${t}_job_proof.json 2>&1 | grep RENDERED; cp out/$t/oval_$k.glb gd/ovals/; done
for k in t1_council t2_banks t3_minor t4_country t5_hub t6_north; do t=${k%%_*}; f=out/$t/proof/turntable_0001-0096.mp4
  if [ $(stat -c %s $f 2>/dev/null || echo 0) -lt 10000 ]; then echo "redo video $t"; python -c "
import json; j=json.load(open('spec/${t}_job_proof.json')); j['views']=[v for v in j['views'] if 'video' in v]; json.dump(j,open('spec/${t}_job_v.json','w'))"
    "$B" -b out/$t/oval_$k.blend -P py/render.py -- spec/${t}_job_v.json 2>&1 | grep RENDERED; fi; done
ls -la out/t*/proof/*.mp4
echo ALLDONE
