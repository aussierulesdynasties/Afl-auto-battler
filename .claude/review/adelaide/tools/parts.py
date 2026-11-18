"""parts.py: one photo|render|50% board per part, cropped from the camera that shows it best"""
import subprocess, sys
P = [('east_stand_roof', 'photos/crop.jpg', 'rend/A_fix.png', '120,580,800,980'),
     ('river_stand_dome', 'photos/crop.jpg', 'rend/A_fix.png', '800,500,1420,800'),
     ('west_stand', 'photos/crop.jpg', 'rend/A_fix.png', '700,680,1430,1120'),
     ('light_towers_A', 'photos/crop.jpg', 'rend/A_fix.png', '40,450,1500,1000'),
     ('west_and_scoreboard_B', 'photos/sweetlime_2024.jpg', 'rend/B_fix.png', '0,900,700,1301'),
     ('river_dome_B', 'photos/sweetlime_2024.jpg', 'rend/B_fix.png', '300,850,650,1100'),
     ('hotel_C', 'close/east_gate_2023.jpg', 'rend/C_fix.png', '1200,800,3700,1500'),
     ('east_roof_back_C', 'close/east_gate_2023.jpg', 'rend/C_fix.png', '1200,450,3840,1050')]
for n, ph, r, c in P:
    subprocess.run([sys.executable, 'tools/board3.py', ph, r, 'proof/part_%s.jpg' % n, c], check=True)
