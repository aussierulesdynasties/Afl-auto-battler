G="C:/Users/DANTE/Desktop/Godot_v4.7.2-stable_win64.exe/Godot_v4.7.2-stable_win64_console.exe"
S=C:/Users/DANTE/AppData/Local/Temp/claude/cec579e0cf1e721a/27ab9b53-76bc-414a-b98e-5c4e22e13159/scratchpad/sub
timeout 300 "$G" --path $S/gproj --windowed --script $S/cu.gd -- "$1" "$2" "$3" 2>&1 | tail -3
