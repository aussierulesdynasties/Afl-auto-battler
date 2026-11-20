cd "/tmp/claude/d00d327f9fc84438/b0e6313e-783e-4879-9574-53fc9d3fcd79/scratchpad/ikon"
for v in A7 B6; do
  "/c/Users/DANTE/Desktop/Godot_v4.7.2-stable_win64.exe/Godot_v4.7.2-stable_win64_console.exe" --windowed --path gp --script C:/Users/DANTE/AppData/Local/Temp/claude/d00d327f9fc84438/b0e6313e-783e-4879-9574-53fc9d3fcd79/scratchpad/ikon/w/turntable.gd -- C:/Users/DANTE/AppData/Local/Temp/claude/d00d327f9fc84438/b0e6313e-783e-4879-9574-53fc9d3fcd79/scratchpad/ikon/w/ikon$v.glb C:/Users/DANTE/AppData/Local/Temp/claude/d00d327f9fc84438/b0e6313e-783e-4879-9574-53fc9d3fcd79/scratchpad/ikon/w/tt$v 4 30 2>&1 | grep -v "^$" | tail -3
done
