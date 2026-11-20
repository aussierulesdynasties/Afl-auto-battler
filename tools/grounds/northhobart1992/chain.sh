cd "$(dirname "$0")"; NH=$(cygpath -m "$PWD"); B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
FF="C:/Users/DANTE/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
rm -f frames/f_*.png
for m in "close r_close.png" "gor r_full_gor.png 1.0" "aerial r_full_aerial.png 1.0" "tt r_tt#.png" "glb northhobart1992.glb"; do set -- $m
  for t in 1 2 3; do "$B" -b --factory-startup --python world2.py -- $NH $1 $NH/$2 ${3:-0.25} > log_$1.txt 2>&1 && grep -q "Blender quit" log_$1.txt && break; done
  echo "$1 $(date +%H:%M) $t"; done
cnt(){ ls frames | grep -cE '^f_[0-9]{4}\.png$'; }
for try in 1 2 3 4 5 6 7 8; do n=$(cnt); [ "$n" -ge 240 ] && break; echo "mp4 try $try $(date +%H:%M) have $n"
  find frames -name 'f_*.png' -size 0 -delete; "$B" -b --factory-startup --python world2.py -- $NH mp4 $NH/frames/f_ 0.25 > log_frames_$try.txt 2>&1; done
n=$(cnt); echo "frames $n $(date +%H:%M)"; [ "$n" -ge 240 ] && "$FF" -y -loglevel error -framerate 30 -i frames/f_%04d.png -c:v libx264 -crf 16 -pix_fmt yuv420p northhobart_exterior.mp4 && ls -la northhobart_exterior.mp4
