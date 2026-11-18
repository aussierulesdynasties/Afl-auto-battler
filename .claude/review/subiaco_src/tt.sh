#!/usr/bin/env bash
# turntable.sh IN.glb OUTDIR NAME : Godot stills then mp4
G="C:/Users/DANTE/Desktop/Godot_v4.7.2-stable_win64.exe/Godot_v4.7.2-stable_win64_console.exe"
T=C:/Users/DANTE/AppData/Local/Temp/claude/cec579e0cf1e721a/27ab9b53-76bc-414a-b98e-5c4e22e13159/scratchpad/sub/tt.gd
FF=C:/Users/DANTE/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe
rm -rf "$2";mkdir -p "$2"
timeout 600 "$G" --path C:/Users/DANTE/AppData/Local/Temp/claude/cec579e0cf1e721a/27ab9b53-76bc-414a-b98e-5c4e22e13159/scratchpad/sub/gproj --windowed --script "$T" -- "$1" "$2" 96 22 0.7 2>&1 | tail -3
"$FF" -y -loglevel error -framerate 24 -i "$2/f%03d.png" -c:v libx264 -pix_fmt yuv420p -crf 18 "$3"
ls -la "$3"
