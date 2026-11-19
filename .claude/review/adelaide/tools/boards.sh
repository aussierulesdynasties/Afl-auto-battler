# boards.sh: after proof.sh and surf.sh, assemble the gate boards into proof/
set -e
python tools/board3.py photos/crop.jpg rend/A_fix.png proof/A_photo_render_overlay.jpg
python tools/board3.py photos/sweetlime_2024.jpg rend/B_fix.png proof/B_photo_render_overlay.jpg
python tools/board3.py close/east_gate_2023.jpg rend/C_fix.png proof/C_photo_render_overlay.jpg
python - <<'EOF'
from PIL import Image
f = [Image.open('rend/turn4/f%03d.png' % i).convert('RGB') for i in range(4)]
w, h = f[0].size; o = Image.new('RGB', (w * 2, h * 2))
for i, im in enumerate(f): o.paste(im, ((i % 2) * w, (i // 2) * h))
o.save('proof/turntable_4.jpg', quality=90)
EOF
PHOTO=hill/cand/big_c09.jpg python tools/ovl.py rend/p/h09.png proof/Hill_c09_overlay.jpg
PHOTO=hill/cand/big_c11.jpg python tools/ovl.py rend/p/h11.png proof/Hill_c11_overlay.jpg
cp rend/p/hill_close.png rend/p/hill_above.png rend/p/closeup_hotel_facade.png rend/p/closeup_west_brick_facade.png proof/
cp rend/j/join_west.png rend/j/join_river.png rend/j/join_east.png proof/
cp rend/top/ovlL.png proof/topdown_overlay.png
python rend/p/signs_board.py && cp rend/p/signs_board.jpg proof/
cp rend/s/texboard.jpg proof/texture_board.jpg
cp rend/s/seats_near.png proof/empty_seats_closeup.png
cp rend/s/seats_far.png proof/empty_seats_far.png
echo BOARDS_DONE
