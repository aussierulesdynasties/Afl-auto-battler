cd /tmp/claude/14b1484a65bfbd74/76476bc6-b87c-4245-8ecb-61de5d49956b/scratchpad/proto
C:/Python314/python.exe -E photo_ov.py
for n in $@; do C:/Python314/python.exe -E ground_job.py optus out/optus/job_ph_$n.json out/optus/job_ph_${n}_g.json >/dev/null
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b out/optus/scene.blend -P render.py -- out/optus/job_ph_${n}_g.json 2>&1 | grep -c Saved
C:/Python314/python.exe -E -c "
from PIL import Image
r=Image.open('out/optus/photo/$n.png').convert('RGB');p=Image.open('ref_optus/$n.jpg').convert('RGB').resize(r.size)
s=Image.new('RGB',(r.width,r.height*3));s.paste(p,(0,0));s.paste(r,(0,r.height));s.paste(Image.blend(p,r,0.5),(0,2*r.height));s.resize((r.width//2,r.height*3//2)).save('out/optus/photo/ov_$n.jpg',quality=85)"; done
