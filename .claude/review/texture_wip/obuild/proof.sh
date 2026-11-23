set -e
cd "$(dirname "$0")";B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe";D=$(pwd -W)
"$B" -b --python build.py -- $D/hout/optus.glb $D/hout/optus.blend 2>&1 | grep -E "^tris" || true
"$B" -b $D/hout/optus.blend --python render.py -- $D/r2/camL.json $D/hout/render.png 2>&1 | grep Saved || true
python board.py hout/render.png hout/board.png; python board.py hout/render.png hout/edges.png edges; python parts.py hout/render.png hout/parts.png
"$B" -b $D/hout/optus.blend --python turn.py -- $D/hout/turn 22 560 0,90,180,270 2>&1 | grep -c Saved || true
python -c "
from PIL import Image
im=[Image.open('hout/turn/turn_%03d.png'%a) for a in (0,90,180,270)];w,h=im[0].size;o=Image.new('RGB',(2*w,2*h))
for k,i in enumerate(im):o.paste(i.convert('RGB'),((k%2)*w,(k//2)*h))
o.save('hout/turn4.png')"
"$B" -b $D/hout/optus.blend --python turn.py -- $D/hout/closeE 8 560 0 1600 900 220 14 97 2 2>&1 | grep -c Saved || true
"$B" -b $D/hout/optus.blend --python turn.py -- $D/hout/closeW 8 560 180 1600 900 220 14 -143 2 2>&1 | grep -c Saved || true
"$B" -b $D/hout/optus.blend --python turn.py -- $D/hout/closeS 5 90 -71 1600 900 35 4 13.6 -108.3 2>&1 | grep -c Saved || true
"$B" -b $D/hout/optus.blend --python turn.py -- $D/hout/endS 14 170 -150 1600 900 50 5 -85.9 -101 2>&1 | grep -c Saved || true
"$B" -b $D/hout/optus.blend --python turn.py -- $D/hout/endN 14 170 100 1600 900 50 5 11.5 107.5 2>&1 | grep -c Saved || true
AZS=$(python -c "print(','.join(str(round(7.5*k,1)) for k in range(48)))")
"$B" -b $D/hout/optus.blend --python turn.py -- $D/hout/spin 22 560 $AZS 1280 720 2>&1 | grep -c Saved || true
python -c "
import glob,subprocess,imageio_ffmpeg,os,shutil
fs=sorted(glob.glob('hout/spin/turn_*.png'),key=lambda f:float(f.split('_')[-1][:-4]));os.makedirs('hout/spinseq',exist_ok=True)
for k,f in enumerate(fs):shutil.copy(f,'hout/spinseq/f_%03d.png'%k)
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-framerate','12','-i','hout/spinseq/f_%03d.png','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','hout/turntable.mp4'],check=True,capture_output=True)
print('mp4',len(fs))"
echo PROOF_DONE
