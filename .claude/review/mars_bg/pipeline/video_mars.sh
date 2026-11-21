cd "D:/Temp/claude/6a5fdc1be2cf0baf/f0b104f0-c447-4a40-a59b-216e29157d33/scratchpad/proto"
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
FF="C:/Users/DANTE/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
"$B" -b out/mars/scene.blend -P render.py -- out/mars/job_fence_g.json 2>&1 | grep -E "RENDERED|rror" | grep -v unregister | tail -2
"$B" -b out/mars/scene.blend -P render.py -- out/mars/job_video.json 2>&1 | grep -E "RENDERED|rror" | grep -v unregister | tail -2
"$FF" -y -loglevel error -framerate 24 -i out/mars/video/orbit_frames/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 20 out/mars/video/mars_orbit.mp4
ls -la out/mars/video/mars_orbit.mp4; echo VIDDONE
