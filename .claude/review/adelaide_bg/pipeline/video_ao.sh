cd "D:/Temp/claude/b012626c2f559e8f/6855d913-d54b-43b8-92a6-1e4e1b34589b/scratchpad/proto/out/adelaide"
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
FF="C:/Users/DANTE/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
"$B" -b scene.blend -P ../../render.py -- job_fence270.json 2>&1 | grep -c Saved
rm -rf video/orbit_frames
"$B" -b scene.blend -P ../../render.py -- job_video.json 2>&1 | grep -E "rror" | grep -v unregister | tail -2
ls video/orbit_frames | wc -l
"$FF" -y -loglevel error -framerate 24 -i video/orbit_frames/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 20 video/adelaide_orbit.mp4
ls -la video/adelaide_orbit.mp4
