set -e
cd "/d/Temp/claude/5e6b242a6aee39ff/9a1244aa-6a65-45a3-a6cb-35aa4e52a3dc/scratchpad/proto"
for g in $@; do
  GLB=$(C:/Python314/python.exe -E -c "import json,os;print(os.path.normpath(json.load(open('spec/$g.json'))['glb']))")
  mkdir -p data/$g/prep; "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P probe_outline.py -- "$GLB" data/$g/prep/footprint.json 2>&1 | grep OUTLINE
  TB=$(C:/Python314/python.exe -E -c "import json;print(' '.join(json.load(open('spec/$g.json')).get('trim_base',[])))"); if [ -n "$TB" ]; then "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P fence_mask.py -- "$GLB" data/$g/prep/fence_polys.json $TB 2>&1 | grep POLYS; C:/Python314/python.exe -E fence_mask.py data/$g/prep/fence_polys.json data/$g/prep/fence_mask.npy; fi
  C:/Python314/python.exe -E -P prep.py spec/$g.json; C:/Python314/python.exe -E bake_ground.py $g
  rm -f out/$g/scene.blend; "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P scene.py -- spec/$g.json 2>&1 | grep -vE "unregister_class|^$" | tail -3; [ -f out/$g/scene.blend ] || { echo SCENE_FAILED; exit 1; }
  "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b out/$g/scene.blend -P render.py -- out/$g/job_stills.json 2>&1 | grep -iE "error|saved" | tail -2
  C:/Python314/python.exe -E -P -c "
from PIL import Image
ims=[Image.open('out/$g/stills/orbit_%03d.png'%i).convert('RGB').resize((800,450)) for i in range(4)]
s=Image.new('RGB',(1600,900))
for i,im in enumerate(ims): s.paste(im,((i%2)*800,(i//2)*450))
s.save('out/$g/stills/sheet.jpg',quality=88)"
  echo built $g
done
