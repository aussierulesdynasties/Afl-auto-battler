set -e
cd /d/Temp/claude/5e6b242a6aee39ff/9a1244aa-6a65-45a3-a6cb-35aa4e52a3dc/scratchpad/proto
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P scene.py -- spec/gmhba.json 2>&1 | grep -E "^pools|SAVED"
cd out/gmhba
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b scene.blend -P ../../render.py -- job_tp3.json 2>&1 | grep RENDERED
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b scene.blend -P ../../render.py -- job_fence.json 2>&1 | grep RENDERED
C:/Python314/python.exe -E /d/Temp/claude/5e6b242a6aee39ff/9a1244aa-6a65-45a3-a6cb-35aa4e52a3dc/scratchpad/py/sheet.py fence fence_sheet.jpg 2
cd ../..
bash video_gmhba.sh
