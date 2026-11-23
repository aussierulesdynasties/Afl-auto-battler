set -e
cd /d/Temp/claude/5e6b242a6aee39ff/9a1244aa-6a65-45a3-a6cb-35aa4e52a3dc/scratchpad/proto
md5sum ../glb/gmhba.glb
true
bash build.sh gmhba
for j in job_34 job_ns job_top job_whole; do "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b out/gmhba/scene.blend -P render.py -- out/gmhba/$j.json 2>&1 | grep -iE "^error|saved" | tail -4; done
