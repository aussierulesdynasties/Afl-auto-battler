#!/usr/bin/env bash
# wait for both Eevee renders, then Godot turntables of each GLB, then mp4s
cd "$(dirname "$0")"
until [ -f rAE.png ] && [ rAE.png -nt spec_A.py ] && [ -f rBE.png ] && [ rBE.png -nt build.py ] && grep -q "quit" logAE.txt && grep -q "quit" logBE.txt; do sleep 5; done
G=/c/Users/DANTE/Desktop/Godot_v4.7.2-stable_win64.exe/Godot_v4.7.2-stable_win64_console.exe
TT=C:/Users/DANTE/AppData/Local/Temp/claude/b6b84c744aa9573f/4f8bf750-ee6b-4915-ab0a-763b88f66195/scratchpad/stadium/turntable.gd
for T in AE BE; do rm -rf tt$T; GPU_SLOT_OWNER=footballpark-2b bash C:/kt/gpu_slot.sh "$G" --windowed --script "$TT" -- "$(cygpath -w $PWD/fp$T.glb)" "$(cygpath -w $PWD/tt$T)" 96 22 0.7 > ttlog$T.txt 2>&1; ls tt$T | wc -l; done
python enc.py
