set -e
cd "$(dirname "$0")"
bash full2.sh model_in5.json h12
bash rt2.sh
G="C:/Users/DANTE/Desktop/Godot_v4.7.2-stable_win64.exe/Godot_v4.7.2-stable_win64_console.exe"
"$G" --path gp --script "$PWD/closeup.gd" -- "$PWD/gabba.glb" "$PWD/cu_seats_n.png" 0.8 63 12 25.8 105 10 2>&1 | grep -iE "^error" | head -3 || true
python -c "
import imageio_ffmpeg, subprocess
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-framerate','30','-i','tt/f%03d.png','-pix_fmt','yuv420p','-crf','18','-vf','scale=trunc(iw/2)*2:trunc(ih/2)*2','gabba_exterior.mp4'],check=True,capture_output=True)"
ls -la gabba_exterior.mp4 cu_seats_n.png h12_board_full.png; echo CHAIN_DONE
