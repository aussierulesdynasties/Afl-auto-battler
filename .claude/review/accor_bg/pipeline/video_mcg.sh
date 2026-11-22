cd "D:/Temp/claude/9cde8b3442051ee1/8e9d400c-05c9-4bcc-aeef-038762663b40/scratchpad/proto"
FF="C:/Users/DANTE/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
for g in mcg; do
 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b out/$g/scene.blend -P render.py -- out/$g/job_video.json 2>&1 | grep -E "RENDERED|rror" | tail -2
 "$FF" -y -loglevel error -framerate 24 -i out/$g/video/orbit_frames/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 20 out/$g/video/${g}_orbit.mp4
 ls -la out/$g/video/${g}_orbit.mp4
done
