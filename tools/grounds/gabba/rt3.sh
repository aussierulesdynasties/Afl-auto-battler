set -e
cd "$(dirname "$0")"
G="C:/Users/DANTE/Desktop/Godot_v4.7.2-stable_win64.exe/Godot_v4.7.2-stable_win64_console.exe"; GL="$PWD/gabba.glb"
"$G" --path gp --script "$PWD/tt.gd" -- "$GL" "$PWD/tt" 120 30 1.35 2>&1 | grep -iE "^error" | head -3 || true
"$G" --path gp --script "$PWD/closeup.gd" -- "$GL" "$PWD/cu_facade.png" 82.37 142.87 5 61.27 103.13 12 2>&1 | grep -iE "^error" | head -3 || true
"$G" --path gp --script "$PWD/closeup.gd" -- "$GL" "$PWD/cu_hyundai.png" -152.44 -0.26 4 -112.49 1.75 10 2>&1 | grep -iE "^error" | head -3 || true
"$G" --path gp --script "$PWD/closeup.gd" -- "$GL" "$PWD/cu_gate.png" $(cat cu_gate.args) 2>&1 | grep -iE "^error" | head -3 || true
"$G" --path gp --script "$PWD/closeup.gd" -- "$GL" "$PWD/cu_screen.png" -6 -45 14 -11.5 -88 9 2>&1 | grep -iE "^error" | head -3 || true
"$G" --path gp --script "$PWD/closeup.gd" -- "$GL" "$PWD/cu_plant.png" -112 -30 38 -134.3 -37.2 22 2>&1 | grep -iE "^error" | head -3 || true
"$G" --path gp --script "$PWD/closeup.gd" -- "$GL" "$PWD/cu_south.png" 150 150 22 118 88 10 2>&1 | grep -iE "^error" | head -3 || true
"$G" --path gp --script "$PWD/closeup.gd" -- "$GL" "$PWD/cu_edge.png" 10.8 8 60 60 80 32 2>&1 | grep -iE "^error" | head -3 || true
ls tt | wc -l; echo DONE
cu() { "$G" --path gp --script "$PWD/closeup.gd" -- "$GL" "$PWD/$1" $2 2>&1 | grep -iE "^error" | head -3 || true; }
cu cu_gate7.png "107 104 4 107.3 81.5 5"
cu cu_seats_w.png "-30 -3 9 -85 -3 16"
cu cu_seats_e.png "40 -10 9 95 -3 16"
cu cu_roof_under.png "-20 20 6 -70 50 30"
cu cu_white.png "140 45 6 121 50 8"
cu cu_navyside.png "125 78 4 112 74 5"
cu cu_roofdeck.png "100 40 40 108 55 15"
cu cu_mast.png "60 120 8 45 95 30"
cu cu_west.png "-150 30 6 -110 10 12"
cu cu_north.png "20 140 6 10 100 14"
cu cu_gate7ne.png "130 98 6 110 74 5"
cu cu_fans.png "112 100 48 117 60 17"
cu cu_fans_low.png "135 75 22 117 59 17"
cu cu_roof_top.png "20 150 75 5 95 30"
echo DONE
