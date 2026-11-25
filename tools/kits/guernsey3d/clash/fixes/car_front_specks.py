"""Carlton clash, front: a fleck of the navy armhole binding inside the white by the right armpit.
    python car_front_specks.py   (work folder, after trace_clash.py)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from despeckle import despeckle

print('CAR front flecks', despeckle('CAR', 'front', 20000, ['#292B36'], [1100, 300, 1700, 1100]), 'px')
