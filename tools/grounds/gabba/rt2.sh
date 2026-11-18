set -e
cd "$(dirname "$0")"
G="C:/Users/DANTE/Desktop/Godot_v4.7.2-stable_win64.exe/Godot_v4.7.2-stable_win64_console.exe"; GL="$PWD/gabba.glb"
rm -rf tt && mkdir tt
"$G" --path gp --script "$PWD/tt.gd" -- "$GL" "$PWD/tt" 120 30 2>&1 | grep -iE "^error" | head -3 || true
"$G" --path gp --script "$PWD/closeup.gd" -- "$GL" "$PWD/cu_facade.png" 82.37 142.87 5 61.27 103.13 12 2>&1 | grep -iE "^error" | head -3 || true
"$G" --path gp --script "$PWD/closeup.gd" -- "$GL" "$PWD/cu_hyundai.png" -152.44 -0.26 4 -112.49 1.75 10 2>&1 | grep -iE "^error" | head -3 || true
"$G" --path gp --script "$PWD/closeup.gd" -- "$GL" "$PWD/cu_gate.png" $(cat cu_gate.args) 2>&1 | grep -iE "^error" | head -3 || true
ls tt | wc -l; echo DONE
