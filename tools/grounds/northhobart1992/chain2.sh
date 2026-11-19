# Full rebuild of the 1992 model and its proof renders (run from anywhere). Textures and geometry first, then Blender.
cd "$(dirname "$0")"; NH=$(cygpath -m "$PWD"); B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
R=../../../.claude/review/north_hobart; mkdir -p $R/renders frames
FF="C:/Users/DANTE/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
PY=C:/Python314/python.exe
$PY textures.py >/dev/null && $PY textures2.py >/dev/null && $PY textures3.py && $PY fence1992.py && $PY geo2.py | head -1 || exit 1
run(){ for t in 1 2 3; do env $1 "$B" -b --factory-startup --python world2.py -- $NH $2 $3 $4 > log_$2.txt 2>&1 && grep -q "Blender quit" log_$2.txt && break; done; echo "$2 $(date +%H:%M) try $t"; }
run X=1 glb $NH/northhobart1992.glb
run X=1 gor $(cygpath -m $R)/renders/r_full_gor.png 1.0
run TRANSP=1 aerial $(cygpath -m $R)/renders/r_full_aerial.png 1.0
run X=1 tt $(cygpath -m $R)/renders/r_tt#.png
run X=1 close $(cygpath -m $R)/renders/r_close.png
rm -f frames/f_*.png
cnt(){ ls frames | grep -cE '^f_[0-9]{4}\.png$'; }
for try in 1 2 3 4 5 6 7 8; do n=$(cnt); [ "$n" -ge 240 ] && break; echo "mp4 try $try $(date +%H:%M) have $n"
  find frames -name 'f_*.png' -size 0 -delete; "$B" -b --factory-startup --python world2.py -- $NH mp4 $NH/frames/f_ 0.25 > log_frames_$try.txt 2>&1; done
n=$(cnt); echo "frames $n $(date +%H:%M)"; [ "$n" -ge 240 ] && "$FF" -y -loglevel error -framerate 30 -i frames/f_%04d.png -c:v libx264 -crf 16 -pix_fmt yuv420p $R/northhobart_turntable.mp4 && ls -la $R/northhobart_turntable.mp4
