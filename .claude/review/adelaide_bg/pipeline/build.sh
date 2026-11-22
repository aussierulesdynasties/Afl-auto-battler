set -e
cd "D:/Temp/claude/b012626c2f559e8f/6855d913-d54b-43b8-92a6-1e4e1b34589b/scratchpad/proto"
for g in $@; do
  GLB=$(C:/Python314/python.exe -E -c "import json,os;print(os.path.normpath(json.load(open('spec/$g.json'))['glb']))")
  mkdir -p data/$g/prep; [ -f data/$g/prep/footprint.json ] || "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P probe_outline.py -- "$GLB" data/$g/prep/footprint.json 2>&1 | grep OUTLINE
  TB=$(C:/Python314/python.exe -E -c "import json;print(' '.join(json.load(open('spec/$g.json')).get('trim_base',[])))"); if [ -n "$TB" ]; then "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P fence_mask.py -- "$GLB" data/$g/prep/fence_polys.json $TB 2>&1 | grep POLYS; C:/Python314/python.exe -E fence_mask.py data/$g/prep/fence_polys.json data/$g/prep/fence_mask.npy; C:/Python314/python.exe -E fence_outline.py data/$g/prep/fence_mask.npy data/$g/prep/fence_outline.json; fi
  C:/Python314/python.exe -E -P prep.py spec/$g.json
  "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P scene.py -- spec/$g.json 2>&1 | grep -vE "unregister_class|^$" | grep -E "surface |courts|shore band|trimmed|trees kept|SAVED|rror|Traceback"
  "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b out/$g/scene.blend -P render.py -- out/$g/job_stills.json 2>&1 | grep -iE "error|saved" | tail -2
  C:/Python314/python.exe -E -P -c "
from PIL import Image
ims=[Image.open('out/$g/stills/orbit_%03d.png'%i).convert('RGB').resize((800,450)) for i in range(4)]
s=Image.new('RGB',(1600,900))
for i,im in enumerate(ims): s.paste(im,((i%2)*800,(i//2)*450))
s.save('out/$g/stills/sheet.jpg',quality=88)"
  echo built $g
done
