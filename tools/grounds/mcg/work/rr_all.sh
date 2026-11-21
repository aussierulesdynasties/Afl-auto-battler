set -e
cd D:/Temp/claude/c705dfb168facc8f/874a7c40-ffe1-4e7f-a2d3-504f6380309b/scratchpad
B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"; W=$(pwd -W)
R=C:/Users/DANTE/Documents/GitHub/Afl-auto-battler/.claude/worktrees/gifted-cori-7b5c34; RV=$R/.claude/review/mcg
(cd model && python paint.py && python paint2.py && python paint3.py && python wallcols.py && python paint4.py && python signs.py) > work/paint_log.txt 2>&1
"$B" -b --python model/rv.py -- "$W/rr" f000 f022 f045 f067 f090 f112 f135 f157 f180 f202 f225 f247 f270 f292 f315 f337 l000 l045 l090 l135 l180 l225 l270 l315 n_0 n_c n_e n_n n_ne n_nw n_s n_se n_sw n_w o000 o045 o090 o135 o180 o225 o270 o315  > work/rv_log.txt 2>&1
python work/ov3.py f000 f022 f045 f067 f090 f112 f135 f157 f180 f202 f225 f247 f270 f292 f315 f337 l000 l045 l090 l135 l180 l225 l270 l315 n_0 n_c n_e n_n n_ne n_nw n_s n_se n_sw n_w o000 o045 o090 o135 o180 o225 o270 o315  > work/ov3_log.txt 2>&1
for v in f000 f022 f045 f067 f090 f112 f135 f157 f180 f202 f225 f247 f270 f292 f315 f337 l000 l045 l090 l135 l180 l225 l270 l315 n_0 n_c n_e n_n n_ne n_nw n_s n_se n_sw n_w o000 o045 o090 o135 o180 o225 o270 o315 ; do cp work/ov3_$v.png $RV/overlays/; done
"$B" -b --python model/rv.py -- "$W/sg" $(cat work/signviews.txt) $(cat work/cornviews.txt) > work/sg_log.txt 2>&1
"$B" -b --python model/rv.py -- "$W/rf" top top_0.22_0.39 > work/rf_log.txt 2>&1
python work/topov.py rf/top_0.22_0.39.png work/topov.png; python work/topov.py rf/top.png work/topov_straight.png
cp work/topov.png $RV/topdown/top_ov_lean.png; cp work/topov_straight.png $RV/topdown/top_ov_straight.png
"$B" -b --python model/proofs_mcg.py -- "$RV" glb stills close joins orbit > work/proofs_log.txt 2>&1
F="C:/Users/DANTE/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
cd $RV && "$F" -y -loglevel error -framerate 24 -i orbit/f%03d.png -c:v libx264 -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" orbit.mp4
cd - && python work/parts.py "$RV/parts" > work/parts_log.txt 2>&1
echo ALLDONE
