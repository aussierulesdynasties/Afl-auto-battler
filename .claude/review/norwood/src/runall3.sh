B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
D="$(pwd -W)"
export SAMPLES=32
"$B" -b --python build.py -- match "$D/r_match" > log_m.txt 2>&1; python trip.py ../main.jpg r_match.png trip_main.png; python crops.py; echo match done $(date +%T)
"$B" -b --python build.py -- turn "$D/r_turn" > log_t.txt 2>&1; echo turn done $(date +%T)
"$B" -b --python build.py -- close "$D/r_close" > close.log 2>&1; echo close done $(date +%T)
"$B" -b --python build.py -- glb "$D/norwood_oval.glb" > log_glb.txt 2>&1; echo glb done $(date +%T)
rm -rf vid; SAMPLES=12 "$B" -b --python build.py -- turnvid "$D/vid" 96 > log_vid.txt 2>&1; echo vid done $(ls vid | wc -l) frames $(date +%T)
FF=$(python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"); "$FF" -y -loglevel error -framerate 24 -i vid/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 turntable.mp4; echo mp4 done $(date +%T)
